/** API proxy route — forwards requests from zkoner.com/api/* to the backend tunnel.
 *  This avoids CORS issues in the browser. */
const BACKEND = "https://polite-rings-argue.loca.lt/api";

export async function GET(request, { params }) {
  const slug = params.slug.join("/");
  const url = `${BACKEND}/${slug}${request.nextUrl.search}`;
  try {
    const resp = await fetch(url, { headers: { "Accept": "application/json" } });
    const data = await resp.json();
    return Response.json(data, { status: resp.status });
  } catch (e) {
    return Response.json({ detail: `Proxy error: ${e.message}` }, { status: 502 });
  }
}

export async function POST(request, { params }) {
  const slug = params.slug.join("/");
  const url = `${BACKEND}/${slug}`;
  try {
    const body = await request.json();
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    return Response.json(data, { status: resp.status });
  } catch (e) {
    return Response.json({ detail: `Proxy error: ${e.message}` }, { status: 502 });
  }
}
