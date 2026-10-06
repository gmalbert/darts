export function BettingOracleFooter() {
  return (
    <div className="page-footer">
      <div className="bo-powered">
        Powered by <a href="https://www.betting-oracle.com" target="_blank" rel="noreferrer">Betting Oracle</a>
      </div>
      <div className="bo-blurb">
        Sports Prediction Analytics<br />
        All content is for informational purposes only and does not constitute betting advice. Wager responsibly.
      </div>
      <a href="https://www.betting-oracle.com" target="_blank" rel="noreferrer">
        <img
          src="https://raw.githubusercontent.com/gmalbert/betting-oracle/main/data_files/logo.png"
          alt="Betting Oracle"
        />
      </a>
    </div>
  );
}

export function RgBanner() {
  return (
    <div className="rg-banner">
      <strong>21+ only.</strong> Gambling involves risk.
      If you or someone you know has a gambling problem,
      call 1-800-GAMBLER or visit{" "}
      <a href="https://www.ncpgambling.org" target="_blank" rel="noreferrer">ncpgambling.org</a>.
    </div>
  );
}

export function AffiliateDisclosure() {
  return (
    <div className="affiliate-notice">
      BullzIQ may earn a commission from DraftKings through referral links.
      This does not affect our model&apos;s picks. Picks are generated independently.
    </div>
  );
}

export function ModelDisclaimer({ inline }: { inline?: boolean }) {
  const text = "Model picks are for informational purposes only and are not guaranteed. Past performance does not predict future results. Bet responsibly.";
  if (inline) return <div className="info-box">{text}</div>;
  return <div className="rg-banner">{text}</div>;
}
