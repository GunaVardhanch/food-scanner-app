"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to MA-Shabari app
    router.push("/aahar");
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-white to-slate-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">MA-Shabari</h1>
        <p className="text-lg text-slate-600 mb-6">Redirecting to your meal planner...</p>
        <div className="flex justify-center items-center gap-2">
          <div className="w-3 h-3 bg-gradient-to-r from-orange-400 to-orange-600 rounded-full animate-bounce"></div>
          <div className="w-3 h-3 bg-gradient-to-r from-green-400 to-green-600 rounded-full animate-bounce" style={{animationDelay: "0.2s"}}></div>
          <div className="w-3 h-3 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full animate-bounce" style={{animationDelay: "0.4s"}}></div>
        </div>
        <p className="mt-8 text-sm text-slate-500">
          If not redirected, <a href="/aahar" className="text-blue-600 underline font-semibold">click here</a>
        </p>
      </div>
    </div>
  );
}

