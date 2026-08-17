import { useState } from "react";
import Upload from "./pages/Upload";
import Analysis from "./pages/Analysis";
import Decision from "./pages/Decision";
import Receipt from "./pages/Receipt";
import Header from "./components/Header";
import StepIndicator from "./components/StepIndicator";
import { PREPARED_CLAIM_ID, isPreparedShowcase, preparedClaim } from "./preparedDemo";

const STEPS = ["Upload", "Analysis", "Decision", "Receipt"];

export default function App() {
  const publicShowcase = isPreparedShowcase();
  const [step, setStep] = useState(0);
  const [claimId, setClaimId] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [isPrepared, setIsPrepared] = useState(false);

  function goTo(nextStep) {
    setStep(nextStep);
    window.scrollTo(0, 0);
  }

  function handleUploaded(id) {
    setIsPrepared(false);
    setClaimId(id);
    goTo(1);
  }

  function handlePreparedDemo() {
    setIsPrepared(true);
    setClaimId(PREPARED_CLAIM_ID);
    goTo(1);
  }

  function handleAnalyzed(data) {
    setAnalysisData(data);
    goTo(2);
  }

  function handleDecisionViewed() {
    goTo(3);
  }

  function handleReset() {
    setStep(0);
    setClaimId(null);
    setAnalysisData(null);
    setIsPrepared(false);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Header prepared={publicShowcase || isPrepared} />
      <div className="max-w-3xl mx-auto px-4 pb-16">
        <StepIndicator steps={STEPS} current={step} />

        {step === 0 && (
          <Upload
            onUploaded={handleUploaded}
            onStartPreparedDemo={handlePreparedDemo}
            publicShowcase={publicShowcase}
          />
        )}
        {step === 1 && (
          <Analysis
            claimId={claimId}
            onAnalyzed={handleAnalyzed}
            prepared={isPrepared ? preparedClaim : null}
          />
        )}
        {step === 2 && (
          <Decision
            data={analysisData}
            onViewReceipt={handleDecisionViewed}
            prepared={isPrepared}
          />
        )}
        {step === 3 && (
          <Receipt
            claimId={claimId}
            onReset={handleReset}
            preparedReceipt={isPrepared ? preparedClaim.receipt : null}
          />
        )}
      </div>
    </div>
  );
}
