/** API proxy route — forwards requests from zkoner.com/api/* to the backend tunnel.
 *  This avoids CORS issues in the browser. */
const BACKEND = "https://polite-rings-argue.loca.lt/api";

export async function GET(request, ctx) {
  const { slug: slugRaw } = await ctx.params;
  const slug = Array.isArray(slugRaw) ? slugRaw.join("/") : String(slugRaw);
  const url = `${BACKEND}/${slug}${request.nextUrl.search}`;
  try {
    const resp = await fetch(url, {
      headers: { "Accept": "application/json", "User-Agent": "ZKONER-Proxy/1.0" },
    });
    const data = await resp.text();
    try {
      return Response.json(JSON.parse(data), { status: resp.status });
    } catch {
      return new Response(data, { status: resp.status, headers: { "Content-Type": "application/json" } });
    }
  } catch (e) {
    return Response.json(
      { detail: `Backend unreachable. ${e.message}` },
      { status: 502, headers: { "Content-Type": "application/json" } },
    );
  }
}

export async function POST(request, ctx) {
  const { slug: slugRaw } = await ctx.params;
  const slug = Array.isArray(slugRaw) ? slugRaw.join("/") : String(slugRaw);
  const url = `${BACKEND}/${slug}${request.nextUrl.search}`;
  try {
    const body = await request.text();
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "User-Agent": "ZKONER-Proxy/1.0" },
      body,
    });
    const data = await resp.text();
    try {
      return Response.json(JSON.parse(data), { status: resp.status });
    } catch {
      return new Response(data, { status: resp.status, headers: { "Content-Type": "application/json" } });
    }
  } catch (e) {
    return Response.json(
      { detail: `Backend unreachable. ${e.message}` },
      { status: 502, headers: { "Content-Type": "application/json" } },
    );
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
