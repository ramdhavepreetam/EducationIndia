import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'
dotenv.config({ path: 'backend/.env' })

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_ANON_KEY

const supabase = createClient(supabaseUrl, supabaseKey)

async function login() {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: 'kavita.ramdhave@paccar.com',
    password: 'Password123!',
  })
  if (error) console.error(error)
  else console.log(data.session.access_token)
}
login()
