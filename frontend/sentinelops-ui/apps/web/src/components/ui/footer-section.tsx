'use client';
import React from 'react';
import type { ComponentProps, ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Github, Youtube, BookOpen, MessageCircle, Shield } from 'lucide-react';
import { AnimatedText } from '@/components/animated-text';

interface FooterLink {
	title: string;
	href: string;
	icon?: React.ComponentType<{ className?: string }>;
}

interface FooterSection {
	label: string;
	links: FooterLink[];
}

const footerLinks: FooterSection[] = [
	{
		label: 'Product',
		links: [
			{ title: 'Overview', href: '/overview' },
			{ title: 'The Build', href: '/build' },
			{ title: 'Pricing', href: '/pricing' },
			{ title: 'Demos', href: '/demos' },
			{ title: 'Try Dashboard', href: '/try-dashboard' },
		],
	},
	{
		label: 'Connect',
		links: [
			{ title: 'GitHub', href: 'https://github.com/cdgtlmda/sentinelops', icon: Github },
			{ title: 'YouTube', href: 'https://youtube.com/@cdgtlmda', icon: Youtube },
			{ title: 'Substack', href: 'https://substack.com/@cdgtlmda', icon: BookOpen },
			{ title: 'Discord', href: 'https://discord.com/users/cdgtlmda', icon: MessageCircle },
		],
	},
];

export function Footer() {
	return (
		<footer className="md:rounded-t-6xl relative w-full max-w-6xl mx-auto flex flex-col items-center justify-center rounded-t-4xl border-t bg-[radial-gradient(35%_128px_at_50%_0%,theme(backgroundColor.white/8%),transparent)] px-6 py-12 lg:py-16">
			<div className="bg-foreground/20 absolute top-0 right-1/2 left-1/2 h-px w-1/3 -translate-x-1/2 -translate-y-1/2 rounded-full blur" />

			<div className="w-full">
				<div className="flex flex-col lg:flex-row lg:justify-between items-start lg:items-start gap-12">
					<AnimatedContainer className="space-y-4">
						<div className="flex items-center gap-2">
							<Shield className="w-8 h-8 text-primary" />
							<span className="text-lg font-semibold font-departure" style={{ fontFamily: 'var(--font-departure-mono), monospace' }}>
								<AnimatedText text="SentinelOps" />
							</span>
						</div>
						<p className="text-muted-foreground text-sm max-w-xs">
							© {new Date().getFullYear()} SentinelOps. All rights reserved.
							<br />
							Advanced Security & Monitoring Platform powered by Google ADK.
						</p>
					</AnimatedContainer>

					<div className="flex flex-wrap gap-12 lg:gap-16">
						{footerLinks.map((section, index) => (
							<AnimatedContainer key={section.label} delay={0.1 + index * 0.1}>
								<div>
									<h3 className="text-sm font-semibold text-foreground mb-4">{section.label}</h3>
									<ul className="text-muted-foreground space-y-2 text-sm">
										{section.links.map((link) => (
											<li key={link.title}>
												<a
													href={link.href}
													className="hover:text-foreground inline-flex items-center transition-all duration-300"
													target={link.href.startsWith('http') ? '_blank' : undefined}
													rel={link.href.startsWith('http') ? 'noopener noreferrer' : undefined}
												>
													{link.icon && <link.icon className="me-1 size-4" />}
													{link.title}
												</a>
											</li>
										))}
									</ul>
								</div>
							</AnimatedContainer>
						))}
					</div>
				</div>
			</div>
		</footer>
	);
}

type ViewAnimationProps = {
	delay?: number;
	className?: ComponentProps<typeof motion.div>['className'];
	children: ReactNode;
};

function AnimatedContainer({ className, delay = 0.1, children }: ViewAnimationProps) {
	const shouldReduceMotion = useReducedMotion();

	if (shouldReduceMotion) {
		return <div className={className}>{children}</div>;
	}

	return (
		<motion.div
			initial={{ filter: 'blur(4px)', y: -8, opacity: 0 }}
			whileInView={{ filter: 'blur(0px)', y: 0, opacity: 1 }}
			viewport={{ once: true }}
			transition={{ delay, duration: 0.8 }}
			className={className}
		>
			{children}
		</motion.div>
	);
} 