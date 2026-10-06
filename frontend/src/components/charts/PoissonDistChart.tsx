import Plot from "react-plotly.js";
import { useTheme } from "../../theme/ThemeProvider";
import { getPlotlyColors } from "../../theme/tokens";

function poissonPmf(k: number, mu: number): number {
  let factorial = 1;
  for (let i = 2; i <= k; i++) factorial *= i;
  return (Math.pow(mu, k) * Math.exp(-mu)) / factorial;
}

interface PoissonDistChartProps {
  mu: number;
  line: number;
  playerName: string;
}

export function PoissonDistChart({ mu, line, playerName }: PoissonDistChartProps) {
  const { theme } = useTheme();
  const colors = getPlotlyColors(theme);

  // Match Streamlit: k_vals = list(range(0, int(expected * 3) + 2))
  const kMax = Math.floor(mu * 3) + 2;
  const kVals: number[] = [];
  for (let k = 0; k <= kMax; k++) kVals.push(k);

  const probs = kVals.map((k) => poissonPmf(k, mu) * 100);
  const barColors = kVals.map((k) => (k > line ? colors.accent : colors.accent2));

  return (
    <Plot
      data={[
        {
          x: kVals,
          y: probs,
          type: "bar",
          marker: { color: barColors },
          name: "P(X=k)",
        },
      ]}
      layout={{
        title: {
          text: `Poisson Distribution \u2014 ${playerName} 180s`,
          font: { color: colors.text, size: 14 },
        },
        xaxis: {
          title: { text: "Number of 180s" },
          gridcolor: colors.grid,
          tickcolor: colors.muted,
          color: colors.muted,
        },
        yaxis: {
          title: { text: "Probability (%)" },
          gridcolor: colors.grid,
          tickcolor: colors.muted,
          color: colors.muted,
        },
        paper_bgcolor: colors.paper_bgcolor,
        plot_bgcolor: colors.plot_bgcolor,
        font: { color: colors.text },
        height: 280,
        margin: { l: 50, r: 10, t: 50, b: 40 },
        showlegend: false,
        shapes: [
          {
            type: "line",
            x0: line,
            x1: line,
            y0: 0,
            y1: 1,
            yref: "paper",
            line: { color: colors.accent2, dash: "dash", width: 2 },
          },
        ],
        annotations: [
          {
            x: line,
            y: 1,
            yref: "paper",
            text: `Line: ${line}`,
            showarrow: false,
            yanchor: "bottom",
            font: { color: colors.accent2, size: 11 },
          },
        ],
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height: 280 }}
      useResizeHandler
    />
  );
}
