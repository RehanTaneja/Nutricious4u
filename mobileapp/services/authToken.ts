import { auth } from './firebase';

// Latest Firebase ID token for the signed-in user. Kept fresh by Firebase's
// onIdTokenChanged listener (which also enables proactive token refresh), so
// synchronous code that builds URLs (e.g. the diet PDF viewer) can use it.
let cachedIdToken: string | null = null;

auth.onIdTokenChanged(async (user) => {
  try {
    cachedIdToken = user ? await user.getIdToken() : null;
  } catch {
    cachedIdToken = null;
  }
});

// Current ID token, or null when signed out / unavailable. Never throws.
export async function getIdTokenSafe(): Promise<string | null> {
  const user = auth.currentUser;
  if (!user) return null;
  try {
    const token = await user.getIdToken();
    cachedIdToken = token;
    return token;
  } catch {
    return cachedIdToken;
  }
}

// Appends ?token=<id token> for backend URLs that are opened directly (no headers possible).
export function withTokenParam(url: string): string {
  if (!cachedIdToken) return url;
  return `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(cachedIdToken)}`;
}
