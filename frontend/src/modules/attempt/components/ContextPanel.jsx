import React from 'react'

export default function ContextPanel({ context, language }) {
    if (!context) return null

    const title = (language === 'mr' && context.title_mr) ? context.title_mr : context.title_en
    const textContext = (language === 'mr' && context.content_mr) ? context.content_mr : context.content_en
    const instruction = (language === 'mr' && context.instruction_mr) ? context.instruction_mr : context.instruction_en
    const imgAlt = (language === 'mr' && context.image_alt_mr) ? context.image_alt_mr : context.image_alt_en

    return (
        <div className="bg-surface-50 p-4 rounded-xl border border-surface-200 shadow-inner h-full overflow-y-auto">
            {instruction && (
                <div className="mb-4 text-sm font-semibold text-brand-600 uppercase tracking-wide">
                    {instruction}
                </div>
            )}

            {title && (
                <h3 className="text-lg font-bold text-surface-900 mb-3">{title}</h3>
            )}

            {context.context_type?.includes('image') || context.image_url ? (
                <div className="my-4 flex justify-center bg-white p-2 rounded border border-surface-100">
                    <img
                        src={context.image_url}
                        alt={imgAlt || 'Context image'}
                        className="max-w-full max-h-96 object-contain"
                    />
                </div>
            ) : null}

            {textContext && (
                <div className="prose prose-sm max-w-none text-surface-700 leading-relaxed whitespace-pre-wrap">
                    {textContext}
                </div>
            )}
        </div>
    )
}
