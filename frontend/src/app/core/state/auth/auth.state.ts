export interface AuthState {
  token: string | null;
  user: any | null;
  loading: boolean;
  error: string | null;
}

export const initialAuthState: AuthState = {
  token: typeof localStorage !== 'undefined' ? localStorage.getItem('auth_token') : null,
  user: null,
  loading: false,
  error: null
};