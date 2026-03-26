export interface AuthState {
  token: string | null;
  user: any | null;
  loading: boolean;
  error: string | null;
}

export const initialAuthState: AuthState = {
  token: localStorage.getItem('auth_token'),
  user: null,
  loading: false,
  error: null
};