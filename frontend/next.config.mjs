/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Docker 슬림 이미지를 위한 독립 실행형 빌드 출력.
  output: "standalone",
};

export default nextConfig;
