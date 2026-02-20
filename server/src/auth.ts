import axios from 'axios';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;
const JWT_SECRET = process.env.JWT_SECRET || 'supersecret';

export const getGitHubAuthUrl = () => {
    return `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&scope=read:user,repo`;
};

export const handleGitHubCallback = async (code: string) => {
    try {
        const tokenResponse = await axios.post(
            'https://github.com/login/oauth/access_token',
            {
                client_id: GITHUB_CLIENT_ID,
                client_secret: GITHUB_CLIENT_SECRET,
                code,
            },
            {
                headers: {
                    Accept: 'application/json',
                },
            }
        );

        const accessToken = tokenResponse.data.access_token;

        const userResponse = await axios.get('https://api.github.com/user', {
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
        });

        const githubUser = userResponse.data;

        // simplistic find or create
        let user = await prisma.user.findUnique({
            where: { githubId: String(githubUser.id) },
        });

        if (!user) {
            user = await prisma.user.create({
                data: {
                    githubId: String(githubUser.id),
                    username: githubUser.login,
                    avatarUrl: githubUser.avatar_url,
                    // major and other fields will be null initially
                },
            });
        }

        const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '1d' });
        return token;
    } catch (error) {
        console.error('GitHub Auth Error:', error);
        throw new Error('Failed to authenticate with GitHub');
    }
};
