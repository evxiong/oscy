import crypto from "crypto";
import { revalidateTag } from "next/cache";
import { NextResponse, type NextRequest } from "next/server";
import * as z from "zod";

const REVALIDATION_SECRET = process.env.REVALIDATION_SECRET!;

const Body = z.object({
  tag: z.string().min(1),
});

type BodyType = z.infer<typeof Body>;

export async function POST(request: NextRequest) {
  try {
    const timestamp = request.headers.get("x-timestamp");
    const signature = request.headers.get("x-signature");

    if (!timestamp || !signature) {
      return NextResponse.json({ error: "Missing headers" }, { status: 400 });
    }

    const bodyText = await request.text();

    if (!verifySignature(signature, timestamp, bodyText)) {
      return NextResponse.json(
        { error: "Invalid or expired signature" },
        { status: 403 },
      );
    }

    const body: BodyType = Body.parse(JSON.parse(bodyText));

    revalidateTag(body.tag);

    return NextResponse.json({ revalidate: true, tag: body.tag });
  } catch (e) {
    console.error(e);
    if (e instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid request body" },
        { status: 400 },
      );
    }
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}

function verifySignature(
  signature: string,
  timestamp: string,
  bodyText: string,
): boolean {
  // only allow request timestamps +/- 30 seconds
  const currentTimestamp = Math.floor(Date.now() / 1000);
  const requestTimestamp = parseInt(timestamp, 10);
  if (Math.abs(currentTimestamp - requestTimestamp) > 30) {
    return false;
  }

  const hmac = crypto.createHmac("sha256", REVALIDATION_SECRET);
  hmac.update(`${timestamp}.${bodyText}`);
  const expected = hmac.digest("hex");

  try {
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expected),
    );
  } catch {
    return false;
  }
}
