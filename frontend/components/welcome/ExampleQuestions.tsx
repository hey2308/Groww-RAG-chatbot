const EXAMPLE_QUESTIONS = [
  "What is the expense ratio of HDFC Large Cap Fund?",
  "What is the minimum SIP amount for HDFC ELSS Tax Saver?",
  "What is the exit load for HDFC Equity Fund?",
];

interface ExampleQuestionsProps {
  onSelect: (question: string) => void;
}

export function ExampleQuestions({ onSelect }: ExampleQuestionsProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Example Questions</h3>
      <div className="space-y-3">
        {EXAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            onClick={() => onSelect(question)}
            className="w-full text-left p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-primary-300 transition-colors duration-200"
          >
            <div className="flex items-center">
              <span className="text-primary-500 mr-3">•</span>
              <span className="text-gray-700">{question}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

