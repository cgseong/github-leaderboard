import express from 'express';
import { PrismaClient } from '@prisma/client';

const router = express.Router();
const prisma = new PrismaClient();

router.get('/overall', async (req, res) => {
    try {
        const users = await prisma.user.findMany({
            orderBy: { totalScore: 'desc' },
            take: 50,
            select: {
                username: true,
                avatarUrl: true,
                totalScore: true,
                major: true,
            },
        });
        res.json(users);
    } catch (error) {
        console.error('Leaderboard error:', error);
        res.status(500).json({ error: 'Failed to fetch leaderboard' });
    }
});

router.get('/major/:major', async (req, res) => {
    const { major } = req.params;
    try {
        const users = await prisma.user.findMany({
            where: { major },
            orderBy: { totalScore: 'desc' },
            take: 50,
            select: {
                username: true,
                avatarUrl: true,
                totalScore: true,
                major: true,
            },
        });
        res.json(users);
    } catch (error) {
        console.error('Leaderboard error:', error);
        res.status(500).json({ error: 'Failed to fetch leaderboard' });
    }
});

export default router;
