import React from 'react';
import { motion } from 'framer-motion';

interface GlowCardProps {
  children: React.ReactNode;
  glowColor: 'blue' | 'purple' | 'green' | 'orange' | 'red';
  customSize?: boolean;
  className?: string;
}

export function GlowCard({ children, glowColor, customSize = false, className = '' }: GlowCardProps) {
  const glowColors = {
    blue: 'shadow-blue-500/20 hover:shadow-blue-500/40 border-blue-500/20',
    purple: 'shadow-purple-500/20 hover:shadow-purple-500/40 border-purple-500/20',
    green: 'shadow-green-500/20 hover:shadow-green-500/40 border-green-500/20',
    orange: 'shadow-orange-500/20 hover:shadow-orange-500/40 border-orange-500/20',
    red: 'shadow-red-500/20 hover:shadow-red-500/40 border-red-500/20',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`
        rounded-xl border bg-card/50 backdrop-blur-sm 
        shadow-lg transition-all duration-300 hover:shadow-2xl
        ${glowColors[glowColor]}
        ${customSize ? '' : 'p-6'}
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
} 