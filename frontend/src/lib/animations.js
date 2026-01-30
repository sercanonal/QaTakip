import { motion, AnimatePresence } from "framer-motion";

// Page transition variants
export const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.3,
    },
  },
};

// Stagger children animation
export const containerVariants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export const itemVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: "easeOut",
    },
  },
};

// Card hover animation
export const cardHoverVariants = {
  rest: {
    scale: 1,
    boxShadow: "0 0 0 rgba(139, 92, 246, 0)",
  },
  hover: {
    scale: 1.02,
    boxShadow: "0 10px 30px rgba(139, 92, 246, 0.15)",
    transition: {
      duration: 0.3,
      ease: "easeOut",
    },
  },
  tap: {
    scale: 0.98,
  },
};

// Fade in animation
export const fadeInVariants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      duration: 0.4,
    },
  },
};

// Slide in from left
export const slideInLeftVariants = {
  initial: {
    opacity: 0,
    x: -30,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
};

// Slide in from right
export const slideInRightVariants = {
  initial: {
    opacity: 0,
    x: 30,
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
};

// Scale animation for buttons/icons
export const scaleVariants = {
  initial: {
    scale: 0,
    opacity: 0,
  },
  animate: {
    scale: 1,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 260,
      damping: 20,
    },
  },
};

// Animated components
export const MotionDiv = motion.div;
export const MotionSection = motion.section;
export const MotionCard = motion.div;
export const MotionButton = motion.button;
export const MotionSpan = motion.span;

// Page wrapper component
export const PageWrapper = ({ children, className = "" }) => (
  <motion.div
    initial="initial"
    animate="animate"
    exit="exit"
    variants={pageVariants}
    className={className}
  >
    {children}
  </motion.div>
);

// Stagger container component
export const StaggerContainer = ({ children, className = "" }) => (
  <motion.div
    initial="initial"
    animate="animate"
    variants={containerVariants}
    className={className}
  >
    {children}
  </motion.div>
);

// Stagger item component
export const StaggerItem = ({ children, className = "" }) => (
  <motion.div variants={itemVariants} className={className}>
    {children}
  </motion.div>
);

// Animated card component
export const AnimatedCard = ({ children, className = "", onClick }) => (
  <motion.div
    initial="rest"
    whileHover="hover"
    whileTap="tap"
    variants={cardHoverVariants}
    className={className}
    onClick={onClick}
  >
    {children}
  </motion.div>
);

// Animated number counter
export const AnimatedNumber = ({ value, className = "" }) => (
  <motion.span
    key={value}
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    className={className}
  >
    {value}
  </motion.span>
);

// Loader animation
export const LoaderAnimation = ({ className = "" }) => (
  <motion.div
    className={className}
    animate={{
      rotate: 360,
    }}
    transition={{
      duration: 1,
      repeat: Infinity,
      ease: "linear",
    }}
  />
);

// Pulse animation
export const PulseAnimation = ({ children, className = "" }) => (
  <motion.div
    className={className}
    animate={{
      scale: [1, 1.05, 1],
    }}
    transition={{
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut",
    }}
  >
    {children}
  </motion.div>
);

export { AnimatePresence };
