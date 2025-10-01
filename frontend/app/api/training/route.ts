// This is a workaround for the dashboard to fetch training jobs
// In a real app, you'd add a GET /api/training endpoint to the backend

export async function GET() {
  // This route doesn't do anything, it's just here to prevent Next.js errors
  // The actual API call is made directly to the backend
  return new Response(JSON.stringify([]), {
    headers: { 'Content-Type': 'application/json' },
  })
}

