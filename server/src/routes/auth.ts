import express from 'express';
import { getGitHubAuthUrl, handleGitHubCallback } from '../auth';

const router = express.Router();

router.get('/github', (req, res) => {
    res.redirect(getGitHubAuthUrl());
});

router.get('/github/callback', async (req, res) => {
    const code = req.query.code as string;
    try {
        const token = await handleGitHubCallback(code);
        // Redirect to frontend with token
        const clientUrl = process.env.CLIENT_URL || 'http://localhost:5173';
        res.redirect(`${clientUrl}/auth/callback?token=${token}`);
    } catch (error) {
        res.status(500).json({ error: 'Authentication failed' });
    }
});

export default router;
