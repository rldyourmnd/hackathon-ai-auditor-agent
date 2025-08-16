'use client';

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, CheckCircle, Zap, BarChart3, MessageSquare, Database } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiService } from "@/lib/store";

export default function Home() {
  const [isSystemHealthy, setIsSystemHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    // Check system health on page load
    ApiService.healthCheck()
      .then(() => setIsSystemHealthy(true))
      .catch(() => setIsSystemHealthy(false));
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Welcome to <span className="text-blue-600">Curestry</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            AI-powered prompt analysis and optimization platform that transforms your prompts
            into high-quality, consistent, and effective instructions for better LLM results.
          </p>
          <div className="flex justify-center gap-4 mb-12">
            <Link href="/analyze">
              <Button size="lg" className="text-lg px-8 py-3">
                Try It Now <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/prompt-base">
              <Button variant="outline" size="lg" className="text-lg px-8 py-3">
                Explore Prompt-base
              </Button>
            </Link>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mb-4">
                  <Zap className="h-8 w-8 text-blue-600" />
                </div>
                <CardTitle>1. Submit Your Prompt</CardTitle>
                <CardDescription>
                  Paste your prompt and let our AI analyze it across multiple dimensions
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mb-4">
                  <BarChart3 className="h-8 w-8 text-green-600" />
                </div>
                <CardTitle>2. Get Detailed Analysis</CardTitle>
                <CardDescription>
                  Receive comprehensive metrics including semantic entropy, contradictions, and quality scores
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mb-4">
                  <CheckCircle className="h-8 w-8 text-purple-600" />
                </div>
                <CardTitle>3. Apply Improvements</CardTitle>
                <CardDescription>
                  Review suggested patches and apply safe fixes to optimize your prompt quality
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>

        {/* Features Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            System Capabilities
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                  Multi-dimensional Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Semantic entropy, contradiction detection, vocabulary analysis, and LLM-as-judge scoring
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2 text-green-600" />
                  Smart Patch Generation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Automated improvement suggestions categorized as safe or risky changes
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2 text-purple-600" />
                  Interactive Clarification
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  AI-generated questions to clarify ambiguous parts of your prompts
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="h-5 w-5 mr-2 text-orange-600" />
                  Prompt-base Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Store, organize, and manage prompt relationships with conflict detection
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="h-5 w-5 mr-2 text-indigo-600" />
                  Multi-format Support
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Works with XML, Markdown, and plain text prompts with format validation
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <ArrowRight className="h-5 w-5 mr-2 text-red-600" />
                  Export & Integration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600">
                  Export optimized prompts in multiple formats (MD, XML, JSON)
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* System Status */}
        <div className="text-center">
          <Card className="inline-block">
            <CardHeader>
              <CardTitle className="flex items-center justify-center">
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  isSystemHealthy === null
                    ? 'bg-yellow-500'
                    : isSystemHealthy
                    ? 'bg-green-500'
                    : 'bg-red-500'
                }`} />
                <span className="font-semibold">
                  {isSystemHealthy === null
                    ? 'Checking...'
                    : isSystemHealthy
                    ? 'All Systems Operational'
                    : 'System Offline'
                  }
                </span>
              </div>
              {isSystemHealthy && (
                <p className="text-sm text-gray-600 mt-2">
                  ✓ Analysis Pipeline Ready ✓ Database Connected ✓ LLM Services Active
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
