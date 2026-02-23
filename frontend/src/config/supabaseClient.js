/**
 * Supabase JS client — single shared instance.
 *
 * ADR-001: Supabase handles all auth (Google, Facebook, Email/Password).
 * FastAPI only validates the JWT. This client is the only place that
 * communicates with Supabase Auth directly.
 *
 * Import this wherever you need Supabase (currently: authStore only).
 * Do NOT import the Supabase client inside API functions — use apiClient instead.
 */
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in .env.local'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
