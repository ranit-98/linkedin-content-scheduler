const SESSION_KEY = 'postpilot-session';

export const hasActiveSession = () => window.localStorage.getItem(SESSION_KEY) === 'active';

export const startSession = () => window.localStorage.setItem(SESSION_KEY, 'active');

export const endSession = () => window.localStorage.removeItem(SESSION_KEY);
