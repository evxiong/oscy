import { NextResponse } from "next/server";
import type { MiddlewareConfig, NextRequest } from "next/server";

export const config: MiddlewareConfig = {
  matcher: ["/api/:path*", "/openapi.json"],
};

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === "/api/docs") {
    return NextResponse.redirect(
      process.env.VERCEL_ENV === "production"
        ? "https://oscy-api.vercel.app/docs"
        : `http://${process.env.API_HOST}:8000/docs`,
    );
  }
  if (request.nextUrl.pathname === "/openapi.json") {
    return NextResponse.rewrite(
      new URL(
        process.env.VERCEL_ENV === "production"
          ? "https://oscy-api.vercel.app/openapi.json"
          : `http://${process.env.API_HOST}:8000/openapi.json`,
      ),
    );
  } else {
    return NextResponse.rewrite(
      new URL(
        process.env.VERCEL_ENV === "production"
          ? `https://oscy-api.vercel.app/${request.nextUrl.pathname.slice(5) + request.nextUrl.search}`
          : `http://${process.env.API_HOST}:8000/${request.nextUrl.pathname.slice(5) + request.nextUrl.search}`,
      ),
    );
  }
}
