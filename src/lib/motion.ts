export const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
} as const;

export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.06 },
  },
} as const;

export const subtleTransition = {
  duration: 0.22,
  ease: [0.22, 1, 0.36, 1] as const,
};
