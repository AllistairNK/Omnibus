export interface AuthState {
  token: string | null;
  user: any | null;
  loading: boolean;
  error: string | null;
}

export const initialAuthState: AuthState = {
  token: typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null,
  user: (() => {
    if (typeof localStorage === 'undefined') return null;
    const userJson = localStorage.getItem('auth_user');
    if (!userJson) return null;
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  })(),
  loading: false,
  error: null
};