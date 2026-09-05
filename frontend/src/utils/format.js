
export const fmtInr = (val) => {
  if (val == null) return "—";
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(val);
};

export const fmtPct = (val) => {
  if (val == null) return "—";
  return `${val}%`;
};
