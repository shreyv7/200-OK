import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useTrellis } from "@/lib/trellis/store";

const pct = (n: number) => `${Math.round(n * 100)}%`;

export function GapBreakdownSheet({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const { gap } = useTrellis();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-xl bg-[#FAFAF8] text-[#111111] border-l border-black/[0.08]">
        <SheetHeader className="border-b border-black/[0.06] pb-5">
          <SheetTitle className="text-xl font-medium tracking-tight text-[#111111]">
            Gap score breakdown
          </SheetTitle>
          <SheetDescription className="text-xs font-mono text-[#666666]">
            Deterministic arithmetic over decayed evidence. 7-day half-life, weighted
            deficit sum.
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 pt-6 pb-10">
          <div className="overflow-hidden rounded-2xl border border-black/[0.08] bg-white">
            <table className="w-full font-mono text-xs">
              <thead className="bg-[#FAFAF8] text-[#9A9A9A] border-b border-black/[0.06]">
                <tr>
                  <th className="p-3.5 text-left font-medium">attribute</th>
                  <th className="p-3.5 text-right font-medium">wᵢ</th>
                  <th className="p-3.5 text-right font-medium">Dᵢ</th>
                  <th className="p-3.5 text-right font-medium">Rᵢ</th>
                  <th className="p-3.5 text-right font-medium">deficit</th>
                  <th className="p-3.5 text-right font-medium">wᵢ·deficit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.04]">
                {(gap.breakdown ?? []).map((b) => (
                  <tr key={b.attributeId} className="hover:bg-[#FAFAF8]/50">
                    <td className="p-3.5 font-medium text-[#111111]">{b.label}</td>
                    <td className="num p-3.5 text-right text-[#666666]">{b.weight.toFixed(2)}</td>
                    <td className="num p-3.5 text-right text-[#666666]">{b.target.toFixed(2)}</td>
                    <td className="num p-3.5 text-right text-[#666666]">{b.revealed.toFixed(3)}</td>
                    <td className="num p-3.5 text-right text-[#666666]">{b.deficit.toFixed(3)}</td>
                    <td className="num p-3.5 text-right text-[#D97706] font-semibold">{b.contribution.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <p className="label-eyebrow">Marker-level evidence</p>
            <div className="mt-3 space-y-2.5">
              {(gap.breakdown ?? []).flatMap((b) =>
                (b.markerEvidence ?? []).map((m) => (
                  <div key={`${b.attributeId}${m.markerId}`} className="flex items-center gap-3">
                    <span className="w-48 shrink-0 truncate font-mono text-xs text-[#666666]">
                      {m.label}
                    </span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-black/[0.06]">
                      <div
                        className="h-full rounded-full bg-[#D97706]"
                        style={{ width: pct(m.strength) }}
                      />
                    </div>
                    <span className="num w-10 text-right font-mono text-xs text-[#111111]">
                      {pct(m.strength)}
                    </span>
                  </div>
                )),
              )}
            </div>
          </div>

          <div>
            <p className="label-eyebrow">Create : Consume</p>
            <div className="mt-3 flex h-3 overflow-hidden rounded-full border border-black/[0.04]">
              <div
                className="bg-[#15803D]"
                style={{ width: pct(gap.createRatio) }}
                title="Create"
              />
              <div
                className="bg-[#D97706]"
                style={{ width: pct(gap.consumeRatio) }}
                title="Consume"
              />
              <div
                className="bg-[#B91C1C]"
                style={{ width: pct(gap.driftRatio) }}
                title="Drift"
              />
            </div>
            <div className="mt-2 flex justify-between font-mono text-[11px] text-[#666666]">
              <span>create {pct(gap.createRatio)}</span>
              <span>consume {pct(gap.consumeRatio)}</span>
              <span>drift {pct(gap.driftRatio)}</span>
            </div>
          </div>

          <div className="rounded-2xl border border-black/[0.08] bg-white p-4 font-mono text-xs leading-relaxed text-[#666666]">
            Rᵢ = min(1, Σ(strength × 0.5^(ageDays/7)) / 3.4)
            <br />
            deficitᵢ = max(0, Dᵢ − Rᵢ)
            <br />
            <span className="text-[#D97706] font-semibold">
              GapScore = round(100 × Σ(wᵢ × deficitᵢ)) = {gap.score}
            </span>
          </div>

          <p className="font-mono text-[11px] text-[#9A9A9A]">
            Simulated evidence set — all events carry <code>simulated: true</code>.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
