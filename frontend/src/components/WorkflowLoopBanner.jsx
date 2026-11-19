import React from 'react';
import { ArrowRight, CheckCircle2, FileUp, Sparkles, UserCheck, ShieldCheck, RefreshCw } from 'lucide-react';

export default function WorkflowLoopBanner({ role = 'USER', activeStep = 1 }) {
  const isReviewer = role === 'REVIEWER' || role === 'ADMIN';

  const userSteps = [
    { number: 1, title: 'Choose Policy', desc: 'Company standard limits' },
    { number: 2, title: 'Enter Bills', desc: 'Category, date & amount' },
    { number: 3, title: 'Attach Receipts', desc: 'Upload proof of payment' },
    { number: 4, title: 'Policy Check', desc: 'Instant rule verification' },
    { number: 5, title: 'Approved & Paid', desc: 'Voucher issued & paid' },
  ];

  const reviewerSteps = [
    { number: 1, title: 'Company Standard', desc: 'Upload policy PDF' },
    { number: 2, title: 'Approve Limits', desc: 'Meals, lodging & caps' },
    { number: 3, title: 'Auto-Check Bills', desc: 'Matches against rules' },
    { number: 4, title: 'Manager Decision', desc: 'Approve or request changes' },
    { number: 5, title: 'Disbursement', desc: 'Authorized payment voucher' },
  ];

  const steps = isReviewer ? reviewerSteps : userSteps;

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4 mb-6">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <RefreshCw className="w-3.5 h-3.5 text-indigo-600 animate-spin-slow" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800 tracking-tight">
              {isReviewer ? 'Reviewer Governance Cycle' : 'Reimbursement Verification Flow'}
            </span>
            <span className="text-[11px] text-slate-400 ml-2">
              {isReviewer
                ? 'Policy Standard ➔ Approve Limits ➔ Automated Match ➔ Review Decision ➔ Disbursement'
                : 'Choose Policy ➔ Enter Bills ➔ Attach Receipts ➔ Policy Check ➔ Approved & Paid'}
            </span>
          </div>
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
          Step {activeStep} of {steps.length}
        </span>
      </div>

      {/* Step Stepper Loop */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 relative">
        {steps.map((s, idx) => {
          const isDone = s.number < activeStep;
          const isCurrent = s.number === activeStep;
          return (
            <div
              key={s.number}
              className={`p-2.5 rounded-lg border transition-all flex items-center gap-2.5 ${
                isCurrent
                  ? 'bg-indigo-50/70 border-indigo-300 text-indigo-900 shadow-xs'
                  : isDone
                  ? 'bg-slate-50 border-slate-200 text-slate-700'
                  : 'bg-white border-slate-200/60 text-slate-400'
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  isCurrent
                    ? 'bg-indigo-600 text-white'
                    : isDone
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-100 text-slate-400 border border-slate-200'
                }`}
              >
                {isDone ? <CheckCircle2 className="w-3.5 h-3.5" /> : s.number}
              </div>
              <div className="min-w-0">
                <p
                  className={`text-xs font-semibold leading-tight truncate ${
                    isCurrent ? 'text-indigo-950 font-bold' : isDone ? 'text-slate-800' : 'text-slate-400'
                  }`}
                >
                  {s.title}
                </p>
                <p className="text-[10px] text-slate-500 truncate leading-tight mt-0.5">{s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
