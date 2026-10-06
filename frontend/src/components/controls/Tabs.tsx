import { useState, type ReactNode, type ReactElement } from "react";

interface TabDef { key: string; label: string; icon?: string }

interface TabPanelProps { tabKey: string; children: ReactNode; }

export function Tabs({ tabs, initial, active: controlledActive, onChange, children }: {
  tabs: TabDef[];
  initial?: string;
  active?: string;
  onChange?: (key: string) => void;
  children: ReactElement<TabPanelProps>[];
}) {
  const [uncontrolled, setUncontrolled] = useState(initial ?? tabs[0].key);
  const active = controlledActive ?? uncontrolled;
  const activeIdx = tabs.findIndex((t) => t.key === active);
  const childArr = Array.isArray(children) ? children : [children];
  const handleSelect = (key: string) => {
    if (onChange) onChange(key);
    else setUncontrolled(key);
  };
  return (
    <>
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab${t.key === active ? " active" : ""}`}
            onClick={() => handleSelect(t.key)}
          >
            {t.icon ? `${t.icon} ` : ""}{t.label}
          </button>
        ))}
      </div>
      {childArr.map((child, idx) =>
        idx === activeIdx
          ? <div key={tabs[idx]?.key ?? idx} className="tab-content active">{child}</div>
          : null
      )}
    </>
  );
}

export function TabPanel({ tabKey, active, children }: { tabKey: string; active: string; children: React.ReactNode }) {
  return <div className={`tab-content${tabKey === active ? " active" : ""}`}>{children}</div>;
}
