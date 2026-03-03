import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import apiClient from '@/config/apiClient'

const messages = {
    upgrade_required_exam: {
        icon: '🔒',
        titleKey: 'upgrade.examRequired.title',
        titleDefault: 'Full Access Required',
        bodyKey: 'upgrade.examRequired.body',
        bodyDefault: 'This paper is available with the full access plan.',
    },
    upgrade_required_attempts: {
        icon: '📋',
        titleKey: 'upgrade.attemptsUsed.title',
        titleDefault: 'Free Attempts Used',
        bodyKey: 'upgrade.attemptsUsed.body',
        bodyDefault: 'You have used all free attempts for this paper.',
    },
    analysis_locked: {
        icon: '📊',
        titleKey: 'upgrade.analysisLocked.title',
        titleDefault: 'Detailed Analysis',
        bodyKey: 'upgrade.analysisLocked.body',
        bodyDefault: 'Topic breakdown and PDF report require full access.',
    },
}

export const UpgradePrompt = ({ reason = 'upgrade_required_exam', onUpgrade }) => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const [priceInr, setPriceInr] = useState(null)

    useEffect(() => {
        apiClient
            .get('/api/catalog/settings/payment_amount_inr')
            .then((res) => setPriceInr(res.data?.value))
            .catch(() => setPriceInr(null))
    }, [])

    const msg = messages[reason] || messages.upgrade_required_exam

    const handleUpgrade = () => {
        if (onUpgrade) {
            onUpgrade()
        } else {
            navigate('/upgrade')
        }
    }

    return (
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-8 text-center shadow-sm">
            <div className="text-5xl mb-4">{msg.icon}</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
                {t(msg.titleKey, msg.titleDefault)}
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
                {t(msg.bodyKey, msg.bodyDefault)}
            </p>
            <button
                onClick={handleUpgrade}
                className="px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all transform hover:scale-105"
            >
                {priceInr
                    ? t('upgrade.cta', `Unlock Full Access — ₹${priceInr}`)
                    : t('upgrade.ctaGeneric', 'Unlock Full Access')}
            </button>
        </div>
    )
}

export default UpgradePrompt
