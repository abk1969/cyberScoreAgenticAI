"use client";

import { scoreToHeatmapColor } from "@/lib/scoring-utils";
import { DOMAIN_LABELS } from "@/lib/constants";
import type { ScoringDomain } from "@/types/scoring";

interface HeatmapVendor {
  vendorId: string;
  vendorName: string;
  domains: Record<ScoringDomain, number>;
}

interface DomainHeatmapProps {
  vendors: HeatmapVendor[];
  className?: string;
}

const DOMAINS: ScoringDomain[] = [
  "network_security",
  "dns_security",
  "web_security",
  "email_security",
  "patching_cadence",
  "ip_reputation",
  "leaks_exposure",
  "regulatory_presence",
];

export function DomainHeatmap({ vendors, className }: DomainHeatmapProps) {
  return (
    <div className={className}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="text-left p-2 font-medium text-muted sticky left-0 bg-white min-w-[140px]">
                Fournisseur
              </th>
              {DOMAINS.map((d) => (
                <th
                  key={d}
                  className="p-2 font-medium text-muted text-center text-xs min-w-[90px]"
                  title={DOMAIN_LABELS[d]}
                >
                  {DOMAIN_LABELS[d].split(" ").slice(-1)[0]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {vendors.map((vendor) => (
              <tr key={vendor.vendorId} className="border-t border-border">
                <td className="p-2 font-medium text-navy sticky left-0 bg-white truncate max-w-[140px]">
                  {vendor.vendorName}
                </td>
                {DOMAINS.map((domain) => {
                  const score = vendor.domains[domain] ?? 0;
                  return (
                    <td key={domain} className="p-1 text-center">
                      <a
                        href={`/vendors/${vendor.vendorId}/scoring?domain=${domain}`}
                        className="block rounded-md p-2 text-white text-xs font-bold transition-transform hover:scale-105"
                        style={{ backgroundColor: scoreToHeatmapColor(score) }}
                        title={`${DOMAIN_LABELS[domain]}: ${score}/100`}
                      >
                        {Math.round(score)}
                      </a>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
