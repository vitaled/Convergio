/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			colors: {
				// Convergio purple/violet brand colors (Design System)
				primary: {
					50: '#f5f3ff',   // Very light purple background
					100: '#ede9fe',  // Light purple tint
					200: '#ddd6fe',  // Soft purple
					300: '#c4b5fd',  // Medium purple
					400: '#a78bfa',  // Bright purple
					500: '#8b5cf6',  // Main purple
					600: '#7c3aed',  // Dark purple
					700: '#6d28d9',  // Darker purple
					800: '#5b21b6',  // Very dark purple
					900: '#4c1d95',  // Deepest purple
					950: '#3730a3'   // Ultra dark purple
				},
				gray: {
					50: '#f8fafc',
					100: '#f1f5f9',
					200: '#e2e8f0',
					300: '#cbd5e1',
					400: '#94a3b8',
					500: '#64748b',
					600: '#475569',
					700: '#334155',
					800: '#1e293b',
					900: '#0f172a',
					950: '#020617'
				},
				// Surface colors for design system
				surface: {
					white: '#ffffff',     // Pure white
					light: '#fcfcfd',     // Off-white
					neutral: '#f8f9fa',   // Light neutral
					border: '#e9ecef',    // Border color
					0: '#ffffff',         // Pure white
					50: '#f8fafc',        // Almost white
					100: '#f1f5f9',       // Very light gray
					200: '#e2e8f0',       // Light gray borders
					300: '#cbd5e1',       // Medium light gray
					400: '#94a3b8',       // Medium gray
					500: '#64748b',       // Base gray
					600: '#475569',       // Dark gray text
					700: '#334155',       // Darker gray
					800: '#1e293b',       // Very dark gray
					900: '#0f172a',       // Almost black
					950: '#020617'        // Near black
				},
				// Semantic colors
				success: {
					50: '#f0fdf4',
					100: '#dcfce7',
					200: '#bbf7d0',
					300: '#86efac',
					400: '#4ade80',
					500: '#10b981',  // Main success green
					600: '#059669',
					700: '#047857',
					800: '#065f46',
					900: '#064e3b'
				},
				warning: {
					50: '#fffbeb',
					100: '#fef3c7',
					200: '#fde68a',
					300: '#fcd34d',
					400: '#fbbf24',
					500: '#f59e0b',  // Main warning orange
					600: '#d97706',
					700: '#b45309',
					800: '#92400e',
					900: '#78350f'
				},
				error: {
					50: '#fef2f2',
					100: '#fee2e2',
					200: '#fecaca',
					300: '#fca5a5',
					400: '#f87171',
					500: '#ef4444',  // Main error red
					600: '#dc2626',
					700: '#b91c1c',
					800: '#991b1b',
					900: '#7f1d1d'
				},
				info: {
					50: '#eff6ff',
					100: '#dbeafe',
					200: '#bfdbfe',
					300: '#93c5fd',
					400: '#60a5fa',
					500: '#3b82f6',  // Main info blue
					600: '#2563eb',
					700: '#1d4ed8',
					800: '#1e40af',
					900: '#1e3a8a'
				}
			},
			fontFamily: {
				// Design system typography
				primary: [
					'JetBrains Mono',
					'Monaco',
					'Consolas',
					'Liberation Mono',
					'Courier New',
					'monospace'
				],
				secondary: [
					'Inter',
					'system-ui',
					'-apple-system',
					'BlinkMacSystemFont',
					'sans-serif'
				],
				sans: [
					'JetBrains Mono',
					'ui-monospace',
					'SFMono-Regular',
					'Monaco',
					'Consolas',
					'Liberation Mono',
					'Courier New',
					'monospace'
				],
				mono: [
					'JetBrains Mono',
					'Fira Code',
					'Monaco',
					'Consolas',
					'Liberation Mono',
					'Courier New',
					'monospace'
				]
			},
			fontSize: {
				// Design system typography scale
				'2xs': ['0.625rem', { lineHeight: '0.75rem' }], // 10px
				xs: ['0.75rem', { lineHeight: '1rem' }],       // 12px
				sm: ['0.875rem', { lineHeight: '1.25rem' }],   // 14px
				base: ['1rem', { lineHeight: '1.5rem' }],      // 16px
				lg: ['1.125rem', { lineHeight: '1.75rem' }],   // 18px
				xl: ['1.25rem', { lineHeight: '1.75rem' }],    // 20px
				'2xl': ['1.5rem', { lineHeight: '2rem' }],     // 24px
				'3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
				'4xl': ['2.25rem', { lineHeight: '2.5rem' }],   // 36px
				'5xl': ['3rem', { lineHeight: '1' }],          // 48px
				'6xl': ['3.75rem', { lineHeight: '1' }],       // 60px
				'7xl': ['4.5rem', { lineHeight: '1' }],        // 72px
				'8xl': ['6rem', { lineHeight: '1' }],          // 96px
				'9xl': ['8rem', { lineHeight: '1' }]           // 128px
			},
			spacing: {
				// Design system spacing scale
				'1': '0.25rem',   // 4px
				'2': '0.5rem',    // 8px
				'3': '0.75rem',   // 12px
				'4': '1rem',      // 16px
				'5': '1.25rem',   // 20px
				'6': '1.5rem',    // 24px
				'8': '2rem',      // 32px
				'10': '2.5rem',   // 40px
				'12': '3rem',     // 48px
				'16': '4rem',     // 64px
				'20': '5rem',     // 80px
				'24': '6rem',     // 96px
				// Extended spacing
				18: '4.5rem',
				88: '22rem',
				128: '32rem'
			},
			maxWidth: {
				'8xl': '88rem',
				'9xl': '96rem'
			},
			animation: {
				'fade-in': 'fadeIn 0.5s ease-in-out',
				'slide-in': 'slideIn 0.3s ease-out',
				'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
				'spin-slow': 'spin 3s linear infinite'
			},
			keyframes: {
				fadeIn: {
					'0%': { opacity: '0' },
					'100%': { opacity: '1' }
				},
				slideIn: {
					'0%': { transform: 'translateY(-10px)', opacity: '0' },
					'100%': { transform: 'translateY(0)', opacity: '1' }
				}
			},
			backdropBlur: {
				xs: '2px'
			},
			borderRadius: {
				// Design system border radius
				'none': '0',
				'sm': '0.375rem',    // 6px
				'DEFAULT': '0.5rem', // 8px
				'md': '0.5rem',      // 8px
				'lg': '0.75rem',     // 12px
				'xl': '1rem',        // 16px
				'2xl': '1.5rem',     // 24px
				'3xl': '1.75rem',    // 28px
				'4xl': '2rem',       // 32px
				'full': '9999px'
			},
		}
	},
	plugins: [
		// Custom CSS variables for theme switching
			function({ addBase, theme }) {
				addBase({
					':root': {
						// Design system CSS variables
						'--font-primary': 'JetBrains Mono, Monaco, Consolas, monospace',
						'--font-secondary': 'Inter, system-ui, sans-serif',
						
						// Purple color palette
						'--color-primary': theme('colors.primary.600'),
						'--color-primary-hover': theme('colors.primary.700'),
						'--color-primary-light': theme('colors.primary.100'),
						'--color-primary-dark': theme('colors.primary.800'),
						
						// Surface colors
						'--bg-primary': theme('colors.surface.white'),
						'--bg-secondary': theme('colors.surface.neutral'),
						'--bg-tertiary': theme('colors.surface.light'),
						
						// Text colors
						'--text-primary': theme('colors.gray.900'),
						'--text-secondary': theme('colors.gray.600'),
						'--text-tertiary': theme('colors.gray.500'),
						
						// Border colors
						'--border-color': theme('colors.surface.border'),
						'--border-light': theme('colors.gray.200'),
						'--border-medium': theme('colors.gray.300'),
						
						// Semantic colors
						'--color-success': theme('colors.success.500'),
						'--color-warning': theme('colors.warning.500'),
						'--color-error': theme('colors.error.500'),
						'--color-info': theme('colors.info.500'),
						
						// Shadow variables
						'--shadow-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
						'--shadow-md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
						'--shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
						'--shadow-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
					},
					'.dark': {
						// Dark mode overrides
						'--color-primary': theme('colors.primary.400'),
						'--color-primary-hover': theme('colors.primary.300'),
						'--color-primary-light': theme('colors.primary.900'),
						'--color-primary-dark': theme('colors.primary.200'),
						
						'--bg-primary': theme('colors.gray.900'),
						'--bg-secondary': theme('colors.gray.800'),
						'--bg-tertiary': theme('colors.gray.700'),
						
						'--text-primary': theme('colors.gray.100'),
						'--text-secondary': theme('colors.gray.300'),
						'--text-tertiary': theme('colors.gray.400'),
						
						'--border-color': theme('colors.gray.700'),
						'--border-light': theme('colors.gray.600'),
						'--border-medium': theme('colors.gray.500'),
						
						// Dark mode shadows with lighter opacity
						'--shadow-sm': '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
						'--shadow-md': '0 4px 6px -1px rgba(0, 0, 0, 0.4)',
						'--shadow-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.4)',
						'--shadow-xl': '0 20px 25px -5px rgba(0, 0, 0, 0.4)'
					}
				})
			}
	]
}