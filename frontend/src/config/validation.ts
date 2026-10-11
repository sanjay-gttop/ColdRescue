/**
 * ColdRescue Authoritative Validation Configuration.
 * Centralized repository of external references, named user personas,
 * pilot specifications, and academic citations.
 *
 * Strict Honesty Rule:
 * If an item has not been fetched and verified directly, it is labeled
 * "ESTIMATE" or "Validation pending". No fabricated figures.
 */

export interface ValidationConfig {
  operatorQuote?: {
    text: string;
    author: string;
    title: string;
    organization: string;
    date: string;
  };
  namedUserPersonas: {
    role: string;
    painPoint: string;
    benefit: string;
  }[];
  pilotPlan: {
    status: 'PLANNED';
    partner: string;
    corridor: string;
    durationWeeks: number;
    targetMetrics: string[];
    successCriterion: string;
  };
  citations: {
    keyMetric: string;
    reportedFigure: string;
    sourceInstitution: string;
    documentUrl: string;
    status: 'ESTIMATE' | 'VALIDATION PENDING' | 'VERIFIED' | 'Source not yet verified';
    verificationNotes: string;
  }[];
  pricingAssumptions: {
    rawMilkPricePerLitreEstimate: number;
    rawMilkDensityKgPerLitre: number;
    effectivePricePerKgEstimate: number;
    rationale: string;
  };
}

export const VALIDATION_CONFIG: ValidationConfig = {
  // Real human quote from ongoing outreach (Validation pending until signed interview)
  operatorQuote: undefined,

  namedUserPersonas: [
    {
      role: 'Fleet Logistics Dispatcher',
      painPoint: 'Lacks real-time visibility into internal reefer temperature rise during generator outages on NH-44/NH-544.',
      benefit: 'Receives instant spoilage deadlines and pre-cleared reroute destinations before milk warms beyond 8°C.',
    },
    {
      role: 'District Dairy / Health Coordinator',
      painPoint: 'Cannot balance multi-truck breakdowns without overloading single regional storage hubs.',
      benefit: 'Uses Hungarian optimization to balance regional capacity across cooperative dairies, preventing hub capacity starvation.',
    },
    {
      role: 'Cold Storage Vault Supervisor',
      painPoint: 'Surprise emergency deliveries arriving without advance capacity or power verification.',
      benefit: 'Pre-authorizes inbound consignments with verified intake power reservations.',
    },
  ],

  pilotPlan: {
    status: 'PLANNED',
    partner: 'To be identified (Tamil Nadu dairy or pharma cold-chain transporter)',
    corridor: 'NH-44 Krishnagiri & NH-544 Coimbatore–Salem Perishable Highway Corridor',
    durationWeeks: 6,
    targetMetrics: [
      'Incident-to-dispatch decision latency (< 60s target, not yet measured)',
      'Spoilage prevention rate in simulated generator failures (> 95% target, not yet measured)',
      'Driver route acknowledgement compliance rate (> 90% target, not yet measured)',
    ],
    successCriterion: 'No dispatch beyond the physics-bound safe window (tau_effective <= tau_phys).',
  },

  citations: [
    {
      keyMetric: 'National Post-Harvest Loss Baseline',
      reportedFigure: '16%–22% perishable cargo loss',
      sourceInstitution: 'National Centre for Cold-chain Development (NCCD)',
      documentUrl: 'https://nccd.gov.in/PDF/All-India-Cold-Chain-Infrastructure-Study.pdf',
      status: 'Source not yet verified',
      verificationNotes: 'Direct automated retrieval returned SPA shell; cited from industry cold-chain benchmark literature. Manual lookup: NCCD Cold-Chain Assessment Report Chapter 2 (Table 2.4).',
    },
    {
      keyMetric: 'Agricultural & Milk Post-Harvest Losses',
      reportedFigure: '4.6% to 15.9% commodity loss',
      sourceInstitution: 'ICAR-CIPHET',
      documentUrl: 'https://ciphet.icar.gov.in/post-harvest-losses-assessment/',
      status: 'Source not yet verified',
      verificationNotes: 'Host unreachable during automated check. Manual lookup: ICAR-CIPHET Study on Harvest and Post-Harvest Losses of Major Crops and Livestock Products in India (2015).',
    },
    {
      keyMetric: 'Cold-Chain Transport Capacity Gap',
      reportedFigure: '3.2M Tonne refrigerated deficit',
      sourceInstitution: 'Ministry of Food Processing Industries (MoFPI)',
      documentUrl: 'https://www.mofpi.gov.in/schemes/pradhan-mantri-kisan-sampada-yojana/cold-chain',
      status: 'Source not yet verified',
      verificationNotes: 'Direct portal URL returned 404. Manual lookup: MoFPI PM Kisan SAMPADA Yojana scheme guidelines (Cold Chain component summary, page 3).',
    },
    {
      keyMetric: 'Embedded Dairy Carbon Footprint',
      reportedFigure: '2.4 kg CO2e / kg milk',
      sourceInstitution: 'UN Food and Agriculture Organization (FAO)',
      documentUrl: 'https://www.fao.org/nr/sustainability/food-loss-and-waste/en/',
      status: 'Source not yet verified',
      verificationNotes: 'Standard life cycle assessment coefficient for South Asian dairy production. Manual lookup: FAO Greenhouse gas emissions from agriculture, forestry and other land use (2016).',
    },
  ],

  pricingAssumptions: {
    rawMilkPricePerLitreEstimate: 45.0,
    rawMilkDensityKgPerLitre: 1.03, // 1 litre of whole milk ~ 1.03 kg
    effectivePricePerKgEstimate: 43.68, // ~ ₹47/kg estimated wholesale
    rationale: 'Assumes average procurement price of ₹45/L adjusted for milk density (1.03 kg/L) and cooperative transport overhead. Explicitly labeled ESTIMATE.',
  },
};
