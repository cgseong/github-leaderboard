import express from 'express';
import { Server } from 'socket.io';

const router = express.Router();

router.post('/github', (req, res) => {
    const event = req.headers['x-github-event'];
    const payload = req.body;

    console.log(`Received GitHub event: ${event}`);

    const io: Server = req.app.get('io');

    if (io) {
        // Determine message based on event
        let message = `New ${event} event`;
        if (event === 'push') {
            message = `New push to ${payload.repository?.full_name}`;
        } else if (event === 'pull_request') {
            message = `New PR ${payload.action} in ${payload.repository?.full_name}`;
        }

        io.emit('leaderboard-update', {
            type: event,
            message: message,
            timestamp: new Date().toISOString()
        });
    }

    res.status(200).send('Webhook received');
});

export default router;
