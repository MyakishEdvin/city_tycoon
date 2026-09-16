import React, { useEffect, useState } from "react";
import { Card } from "../components";
import { useAppData } from "../appData";
import { useI18n } from "../i18n";
import { fetchTransactions } from "../api";
import type { TransactionOut } from "../types";

function formatTransaction(tx: TransactionOut): string {
  const sign = tx.amount >= 0 ? "+" : "-";
  const label = tx.type.replace(/_/g, " ");
  return `${sign}$${Math.abs(tx.amount).toLocaleString()} — ${label}`;
}

export default function Balance(): React.JSX.Element {
  const { me, loading: meLoading, error: meError } = useAppData();
  const { t } = useI18n();
  const [transactions, setTransactions] = useState<TransactionOut[] | null>(null);
  const [txError, setTxError] = useState<string | null>(null);

  useEffect(() => {
    fetchTransactions(20, 0)
      .then((res) => setTransactions(res.items))
      .catch((err) => setTxError(err instanceof Error ? err.message : "Unknown error"));
  }, []);

  if (meLoading) return <div className="screen-state">{t("common.loading")}</div>;
  if (meError || !me) return <div className="screen-state">{t("common.error")}</div>;

  return (
    <div className="screen">
      <div className="hero-card">
        <div className="hero-label">{t("balance.title")}</div>
        <div className="hero-value">${me.money.toLocaleString()}</div>
      </div>

      <Card>
        <h3>{t("balance.recentTransactions")}</h3>
        {txError && <p className="muted-note">{t("common.error")}</p>}
        {!txError && transactions !== null && transactions.length === 0 && (
          <p className="muted-note">{t("balance.noTransactions")}</p>
        )}
        {transactions !== null && transactions.length > 0 && (
          <ul className="transaction-list">
            {transactions.map((tx) => (
              <li key={tx.id} className={tx.amount >= 0 ? "tx-positive" : "tx-negative"}>
                <span>{formatTransaction(tx)}</span>
                <span className="tx-date">
                  {new Date(tx.created_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}