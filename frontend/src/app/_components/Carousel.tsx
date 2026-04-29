import Image from "next/image";
import type { ImageInfo } from "../_utils/utils";

export function Carousel({ images }: { images: ImageInfo[] }) {
  const rotateFactor = 360 / images.length;
  return (
    <div
      className="relative h-full w-full overflow-hidden"
      style={{
        perspective: "1000px",
        maskImage:
          "linear-gradient(to right, rgba(0, 0, 0, 0.5) 0%, rgb(0, 0, 0) 10%, rgb(0, 0, 0) 90%, rgba(0, 0, 0, 0.5) 100%)",
      }}
    >
      <div
        className="rotate-carousel relative h-full w-full"
        style={{ transformStyle: "preserve-3d" }}
      >
        {images.map((image, i) => {
          const rotateY = -(rotateFactor * i);
          return (
            <div
              key={i}
              className="absolute left-1/2 top-1/2"
              style={{
                transform: `translate(-50%, -50%) rotateY(${rotateY}deg) translateZ(-700px)`,
                backfaceVisibility: "hidden",
              }}
            >
              <div className="relative h-[320px] w-[216px] overflow-hidden rounded-md border border-border shadow-md">
                <Image
                  src={image.src}
                  draggable={false}
                  fill={true}
                  alt={image.alt}
                  priority={true}
                  className="object-cover"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
