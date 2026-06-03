import { Bot } from "lucide-react";

export function WelcomeMessage() {
  return (
    <div className="mb-8 text-center">
      <Bot className="w-16 h-16 text-primary-500 mx-auto mb-4" />
      <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Mutual Fund FAQ Assistant</h2>
      <p className="text-lg text-gray-600 max-w-2xl mx-auto">
        Ask objective questions about HDFC mutual funds like expense ratio, minimum SIP, exit load,
        riskometer, and benchmark details.
      </p>
    </div>
  );
}

