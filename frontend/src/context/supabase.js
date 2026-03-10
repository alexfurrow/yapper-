import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables (VITE_SUPABASE_URL and/or VITE_SUPABASE_PUBLISHABLE_KEY). Please check your .env file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
