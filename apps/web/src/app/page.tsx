import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8f9fa] to-[#fff4cc] p-8 font-sans text-gray-800 flex flex-col items-center justify-center">
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="text-6xl font-light text-gray-900 tracking-tight">
          Code<span className="font-bold">Atlas</span>
        </h1>
        <p className="text-xl text-gray-600 font-light">
          The "Google Maps" for your software codebase. Automatically analyze, map, and chat with your entire architecture.
        </p>
        
        <div className="flex justify-center space-x-4 pt-8">
          <Link href="/login" className="px-8 py-4 bg-gray-900 text-white rounded-full font-medium hover:bg-gray-800 transition shadow-lg">
            Login
          </Link>
          <Link href="/register" className="px-8 py-4 bg-white text-gray-900 rounded-full font-medium hover:bg-gray-50 transition shadow-sm border border-gray-200">
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
}
