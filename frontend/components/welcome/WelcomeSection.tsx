import { ExampleQuestions } from "./ExampleQuestions";
import { WelcomeMessage } from "./WelcomeMessage";

interface WelcomeSectionProps {
  onSelectExample: (question: string) => void;
}

export function WelcomeSection({ onSelectExample }: WelcomeSectionProps) {
  return (
    <section className="flex-1 flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <WelcomeMessage />
        <ExampleQuestions onSelect={onSelectExample} />
      </div>
    </section>
  );
}

