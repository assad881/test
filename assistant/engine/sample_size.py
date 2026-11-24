"""Sample size calculator (AsaadStat).

Usage examples:
  python sample_size.py proportion --p 0.5 --margin 0.05 --population 3200 --nonresponse 0.1
  python sample_size.py two-proportions --p1 0.30 --p2 0.45 --power 0.8
  python sample_size.py two-means --sd 12 --diff 5 --power 0.8
  python sample_size.py correlation --r 0.25 --power 0.8
  python sample_size.py logistic --predictors 8 --event-rate 0.3     (Peduzzi EPV=10)
"""
import argparse
import math

from scipy.stats import norm


def z(a):
    return norm.isf(a)


def single_proportion(p, margin, conf=0.95, population=None, deff=1.0):
    n0 = z((1 - conf) / 2) ** 2 * p * (1 - p) / margin**2 * deff
    n = n0 / (1 + (n0 - 1) / population) if population else n0
    return n0, n


def two_proportions(p1, p2, alpha=0.05, power=0.8, ratio=1.0):
    pbar = (p1 + ratio * p2) / (1 + ratio)
    za, zb = z(alpha / 2), z(1 - power)
    n1 = (za * math.sqrt(pbar * (1 - pbar) * (1 + 1 / ratio))
          + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)) ** 2 / (p1 - p2) ** 2
    return n1, n1 * ratio


def two_means(sd, diff, alpha=0.05, power=0.8, ratio=1.0):
    n1 = (1 + 1 / ratio) * (z(alpha / 2) + z(1 - power)) ** 2 * sd**2 / diff**2
    return n1, n1 * ratio


def correlation(r, alpha=0.05, power=0.8):
    c = 0.5 * math.log((1 + r) / (1 - r))
    return ((z(alpha / 2) + z(1 - power)) / c) ** 2 + 3


def inflate(n, nonresponse):
    return math.ceil(n / (1 - nonresponse)) if nonresponse else math.ceil(n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="kind", required=True)
    s = sub.add_parser("proportion")
    s.add_argument("--p", type=float, default=0.5)
    s.add_argument("--margin", type=float, default=0.05)
    s.add_argument("--conf", type=float, default=0.95)
    s.add_argument("--population", type=int)
    s.add_argument("--deff", type=float, default=1.0)
    s = sub.add_parser("two-proportions")
    s.add_argument("--p1", type=float, required=True)
    s.add_argument("--p2", type=float, required=True)
    s = sub.add_parser("two-means")
    s.add_argument("--sd", type=float, required=True)
    s.add_argument("--diff", type=float, required=True)
    s = sub.add_parser("correlation")
    s.add_argument("--r", type=float, required=True)
    s = sub.add_parser("logistic")
    s.add_argument("--predictors", type=int, required=True)
    s.add_argument("--event-rate", type=float, required=True)
    s.add_argument("--epv", type=int, default=10)
    for name in ("two-proportions", "two-means", "correlation"):
        sp = sub.choices[name]
        sp.add_argument("--alpha", type=float, default=0.05)
        sp.add_argument("--power", type=float, default=0.8)
    for name in ("two-proportions", "two-means"):
        sub.choices[name].add_argument("--ratio", type=float, default=1.0)
    for sp in sub.choices.values():
        sp.add_argument("--nonresponse", type=float, default=0.0)
    a = ap.parse_args()

    if a.kind == "proportion":
        n0, n = single_proportion(a.p, a.margin, a.conf, a.population, a.deff)
        print(f"Cochran n0 = {n0:.1f}")
        if a.population:
            print(f"Finite population correction (N={a.population}) → n = {n:.1f}")
        print(f"Final sample (non-response {a.nonresponse:.0%}) = {inflate(n, a.nonresponse)}")
        print(f"\nMethods text: The sample size was calculated using Cochran's formula assuming an "
              f"expected proportion of {a.p:.0%}, a {a.conf:.0%} confidence level and a margin of error "
              f"of {a.margin:.0%}" + (f", with finite population correction (N = {a.population})" if a.population else "")
              + (f" and a design effect of {a.deff}" if a.deff != 1 else "")
              + f". Allowing for {a.nonresponse:.0%} non-response, the required sample was "
              f"{inflate(n, a.nonresponse)} participants.")
    elif a.kind == "two-proportions":
        n1, n2 = two_proportions(a.p1, a.p2, a.alpha, a.power, a.ratio)
        print(f"Group 1 = {inflate(n1, a.nonresponse)}, Group 2 = {inflate(n2, a.nonresponse)} "
              f"(α={a.alpha}, power={a.power:.0%}, p1={a.p1}, p2={a.p2})")
    elif a.kind == "two-means":
        n1, n2 = two_means(a.sd, a.diff, a.alpha, a.power, a.ratio)
        print(f"Group 1 = {inflate(n1, a.nonresponse)}, Group 2 = {inflate(n2, a.nonresponse)} "
              f"(α={a.alpha}, power={a.power:.0%}, SD={a.sd}, Δ={a.diff}, d={a.diff / a.sd:.2f})")
    elif a.kind == "correlation":
        print(f"n = {inflate(correlation(a.r, a.alpha, a.power), a.nonresponse)} "
              f"(r={a.r}, α={a.alpha}, power={a.power:.0%})")
    elif a.kind == "logistic":
        n = a.epv * a.predictors / a.event_rate
        print(f"n = {inflate(n, a.nonresponse)} (EPV={a.epv}, predictors={a.predictors}, "
              f"event rate={a.event_rate:.0%}; Peduzzi et al., 1996)")


if __name__ == "__main__":
    main()
