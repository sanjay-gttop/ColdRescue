import { ChevronRightIcon, ThermometerIcon } from '../common/Icons';

interface TruckHeroProps {
  incidentId: string;
  cargoDesc: string;
  currentTempC: number;
  safeLimitC: number;
  onLaunchCommandCenter: () => void;
  onExploreWorkflow: () => void;
}

export const TruckHero: React.FC<TruckHeroProps> = ({
  incidentId,
  cargoDesc,
  currentTempC,
  safeLimitC,
  onLaunchCommandCenter,
  onExploreWorkflow,
}) => {
  return (
    <section
      aria-label="Refrigerated Truck Emergency Rescue Hero"
      className="card"
      style={{
        position: 'relative',
        overflow: 'hidden',
        padding: '36px 32px',
        background: 'linear-gradient(135deg, rgba(13, 18, 31, 0.98) 0%, rgba(7, 9, 14, 0.95) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.18)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.7), 0 0 60px -15px rgba(56, 189, 248, 0.12)',
      }}
    >
      {/* Background Radial Glow Spotlight */}
      <div
        style={{
          position: 'absolute',
          top: '-15%',
          right: '5%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(56, 189, 248, 0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      <div
        style={{
          position: 'relative',
          zIndex: 1,
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.15fr) minmax(0, 0.85fr)',
          gap: '32px',
          alignItems: 'center',
        }}
      >
        {/* Left Column: Frame.io Editorial Copy & CTAs */}
        <div>
          {/* Micro Category Label */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: currentTempC > safeLimitC ? 'var(--status-critical)' : 'var(--accent-cyan)',
                boxShadow: currentTempC > safeLimitC ? '0 0 8px var(--status-critical)' : '0 0 8px var(--accent-cyan)',
              }}
            />
            <span className="micro-label" style={{ color: 'var(--accent-cyan)' }}>
              LIVE COLD-CHAIN RESPONSE SYSTEM • NH-44 CORRIDOR
            </span>
          </div>

          {/* Large, Restrained, Modern Headline */}
          <h1
            style={{
              fontSize: '2.5rem',
              fontWeight: 850,
              letterSpacing: '-0.035em',
              lineHeight: 1.15,
              color: '#ffffff',
              marginBottom: '16px',
            }}
          >
            Protect the cold chain.{' '}
            <span style={{ color: 'var(--accent-cyan)', display: 'block' }}>
              Coordinate the recovery.
            </span>
          </h1>

          {/* Supporting Text */}
          <p
            style={{
              fontSize: '1.05rem',
              lineHeight: 1.6,
              color: 'var(--text-secondary)',
              maxWidth: '540px',
              marginBottom: '28px',
            }}
          >
            Evaluate recovery windows, compare feasible allocations, and coordinate human-approved responses.
          </p>

          {/* Primary & Secondary Action CTAs */}
          <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={onLaunchCommandCenter}
              className="btn btn-primary"
              style={{
                padding: '12px 24px',
                fontSize: '0.95rem',
                fontWeight: 700,
                borderRadius: 'var(--radius-sm)',
                boxShadow: '0 0 20px rgba(56, 189, 248, 0.35)',
              }}
            >
              <span>Launch Command Center</span>
              <ChevronRightIcon size={16} />
            </button>

            <button
              onClick={onExploreWorkflow}
              className="btn btn-secondary"
              style={{
                padding: '12px 22px',
                fontSize: '0.95rem',
                fontWeight: 600,
                borderRadius: 'var(--radius-sm)',
              }}
            >
              Explore the workflow
            </button>
          </div>

          {/* Invariant Confidence Bar */}
          <div
            style={{
              marginTop: '28px',
              paddingTop: '18px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              gap: '24px',
              alignItems: 'center',
            }}
          >
            <div>
              <span className="micro-label">GOVERNING INVARIANT</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                min(Physics, ML Surrogate)
              </div>
            </div>
            <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-subtle)' }} />
            <div>
              <span className="micro-label">SOLVER RIGOR</span>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--status-safe)', marginTop: '2px' }}>
                Kuhn-Munkres Exact Optimal
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Cinematic Refrigerated Truck Showcase with Cool Industrial Lighting */}
        <div
          style={{
            position: 'relative',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden',
            border: '1px solid rgba(56, 189, 248, 0.22)',
            backgroundColor: '#0a0e17',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
          }}
        >
          {/* Stylized High-Detail SVG Reel: Peterbilt Style Reefer Truck in Cool Industrial Midnight Lighting */}
          <svg
            viewBox="0 0 540 320"
            style={{ width: '100%', height: 'auto', display: 'block' }}
            role="img"
            aria-label="Cinematic Refrigerated Reefer Truck under cool industrial spotlight"
          >
            <defs>
              <linearGradient id="truckBodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="60%" stopColor="#0f172a" />
                <stop offset="100%" stopColor="#090d16" />
              </linearGradient>

              <linearGradient id="chillerGlow" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#0284c7" stopOpacity="0.2" />
              </linearGradient>

              <linearGradient id="spotlightCone" x1="50%" y1="0%" x2="50%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.3" />
                <stop offset="80%" stopColor="#0284c7" stopOpacity="0.05" />
                <stop offset="100%" stopColor="transparent" stopOpacity="0" />
              </linearGradient>

              <radialGradient id="wheelGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                <stop offset="100%" stopColor="transparent" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Midnight Sky & Ambient Grid */}
            <rect width="540" height="320" fill="#07090e" />
            
            {/* Top Atmospheric Industrial Lighting Beam */}
            <polygon points="120,0 420,0 490,260 50,260" fill="url(#spotlightCone)" />

            {/* Road Surface */}
            <rect x="0" y="250" width="540" height="70" fill="#0a0f18" />
            <line x1="0" y1="250" x2="540" y2="250" stroke="#1e293b" strokeWidth="2" />
            {/* Road Markings */}
            <line x1="40" y1="285" x2="110" y2="285" stroke="#38bdf8" strokeWidth="2" strokeDasharray="14 10" opacity="0.6" />
            <line x1="160" y1="285" x2="230" y2="285" stroke="#38bdf8" strokeWidth="2" strokeDasharray="14 10" opacity="0.6" />
            <line x1="280" y1="285" x2="350" y2="285" stroke="#38bdf8" strokeWidth="2" strokeDasharray="14 10" opacity="0.6" />
            <line x1="400" y1="285" x2="470" y2="285" stroke="#38bdf8" strokeWidth="2" strokeDasharray="14 10" opacity="0.6" />

            {/* Shadow under Truck */}
            <ellipse cx="270" cy="254" rx="220" ry="12" fill="#000000" opacity="0.75" />

            {/* REEFER TRAILER BODY */}
            <rect x="80" y="85" width="290" height="135" rx="4" fill="url(#truckBodyGrad)" stroke="#334155" strokeWidth="1.5" />
            
            {/* Insulated Panels Grooves */}
            <line x1="140" y1="85" x2="140" y2="220" stroke="#1e293b" strokeWidth="1" />
            <line x1="200" y1="85" x2="200" y2="220" stroke="#1e293b" strokeWidth="1" />
            <line x1="260" y1="85" x2="260" y2="220" stroke="#1e293b" strokeWidth="1" />
            <line x1="320" y1="85" x2="320" y2="220" stroke="#1e293b" strokeWidth="1" />

            {/* Trailer Roof Aero Cap */}
            <path d="M 80 85 L 120 75 L 370 75 L 370 85 Z" fill="#1e293b" stroke="#334155" strokeWidth="1" />

            {/* Carrier Transicold Chiller Unit on Front of Trailer */}
            <rect x="365" y="95" width="20" height="70" rx="3" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
            {/* Chiller Status Light Glow */}
            <circle cx="375" cy="110" r="4" fill="#38bdf8" />
            <line x1="370" y1="125" x2="380" y2="125" stroke="#e2e8f0" strokeWidth="1.5" />
            <line x1="370" y1="135" x2="380" y2="135" stroke="#e2e8f0" strokeWidth="1.5" />
            <line x1="370" y1="145" x2="380" y2="145" stroke="#e2e8f0" strokeWidth="1.5" />

            {/* ColdRescue Fleet Identity on Trailer */}
            <text x="110" y="145" fill="#ffffff" fontSize="20" fontWeight="900" letterSpacing="1">
              COLD<tspan fill="#38bdf8">RESCUE</tspan>
            </text>
            <text x="110" y="165" fill="#64748b" fontSize="9" fontWeight="700" letterSpacing="1.5">
              AUTONOMOUS THERMAL RESILIENCE
            </text>

            {/* PULL TRACTOR / CABIN (Peterbilt Long-Nose Style) */}
            {/* Sleeper Box */}
            <rect x="375" y="115" width="55" height="105" rx="3" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
            {/* Day Cab / Windshield Area */}
            <path d="M 430 140 L 445 160 L 485 165 L 485 220 L 430 220 Z" fill="#0f172a" stroke="#334155" strokeWidth="1.5" />
            {/* Windshield Glass */}
            <polygon points="432,143 444,162 470,165 465,143" fill="#38bdf8" opacity="0.35" stroke="#38bdf8" strokeWidth="0.8" />
            
            {/* Peterbilt Long Hood / Grille */}
            <path d="M 470 170 L 498 175 L 498 220 L 470 220 Z" fill="#1e293b" stroke="#475569" strokeWidth="1.2" />
            {/* Chrome Grille Bars */}
            <rect x="495" y="178" width="5" height="38" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="0.5" />

            {/* Heavy-Duty Dual Chrome Vertical Exhaust Stacks */}
            <rect x="378" y="55" width="4" height="65" rx="1.5" fill="#cbd5e1" stroke="#94a3b8" strokeWidth="0.5" />
            <rect x="384" y="55" width="4" height="65" rx="1.5" fill="#94a3b8" stroke="#64748b" strokeWidth="0.5" />

            {/* Aerodynamic Roof Deflector on Cab */}
            <polygon points="380,85 435,115 380,115" fill="#0f172a" stroke="#334155" strokeWidth="1" />

            {/* Headlights High-Power Beam */}
            <polygon points="498,202 540,195 540,245 498,212" fill="url(#chillerGlow)" opacity="0.45" />

            {/* WHEEL HUBS WITH CHROME RIMS */}
            {/* Trailer Rear Tandem Wheels */}
            <circle cx="115" cy="235" r="20" fill="#020617" stroke="#475569" strokeWidth="2" />
            <circle cx="115" cy="235" r="10" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />
            <circle cx="160" cy="235" r="20" fill="#020617" stroke="#475569" strokeWidth="2" />
            <circle cx="160" cy="235" r="10" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />

            {/* Tractor Drive Tandem Wheels */}
            <circle cx="395" cy="235" r="20" fill="#020617" stroke="#475569" strokeWidth="2" />
            <circle cx="395" cy="235" r="10" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />
            <circle cx="435" cy="235" r="20" fill="#020617" stroke="#475569" strokeWidth="2" />
            <circle cx="435" cy="235" r="10" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />

            {/* Tractor Front Steer Wheel */}
            <circle cx="485" cy="235" r="19" fill="#020617" stroke="#475569" strokeWidth="2" />
            <circle cx="485" cy="235" r="9" fill="#1e293b" stroke="#38bdf8" strokeWidth="1" />

            {/* Sensor Telemetry Indicator Pin */}
            <circle cx="200" cy="85" r="5" fill="#f43f5e" />
            <circle cx="200" cy="85" r="10" fill="none" stroke="#f43f5e" strokeWidth="1" opacity="0.6">
              <animate attributeName="r" values="5;14;5" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
          </svg>

          {/* Real Telemetry Floating Glass HUD Overlay */}
          <div
            style={{
              position: 'absolute',
              bottom: '12px',
              left: '12px',
              right: '12px',
              background: 'rgba(11, 15, 25, 0.82)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(148, 163, 184, 0.18)',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ThermometerIcon size={16} />
              <div>
                <span className="micro-label" style={{ display: 'block', fontSize: '0.62rem' }}>
                  CORE TELEMETRY
                </span>
                <span style={{ fontSize: '0.86rem', fontWeight: 800, color: currentTempC > safeLimitC ? 'var(--status-critical)' : 'var(--status-safe)' }}>
                  {currentTempC.toFixed(1)}°C{' '}
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    (Limit: {safeLimitC.toFixed(1)}°C)
                  </span>
                </span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span className="micro-label" style={{ display: 'block', fontSize: '0.62rem' }}>
                ACTIVE UNIT
              </span>
              <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {incidentId} • {cargoDesc}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
