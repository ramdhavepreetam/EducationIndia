const ChildSwitcher = ({ children, selectedChildId, onSelect, onAddChild }) => {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1
                    scrollbar-hide mb-6">
      {children.map(child => {
        const isSelected = child.student_id === selectedChildId
        const label = child.child_nickname || child.full_name
        const classLabel = child.std_class ? `${child.std_class}th` : null

        return (
          <button
            key={child.student_id}
            onClick={() => onSelect(child.student_id)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-full
              text-sm font-medium whitespace-nowrap transition-all
              ${isSelected
                ? 'bg-blue-600 text-white shadow-md shadow-blue-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }
            `}
          >
            {/* Avatar initial circle */}
            <span className={`
              w-6 h-6 rounded-full flex items-center justify-center
              text-xs font-bold
              ${isSelected ? 'bg-white/20 text-white' : 'bg-gray-300 text-gray-600'}
            `}>
              {label[0].toUpperCase()}
            </span>

            {label}

            {/* Class badge */}
            {classLabel && (
              <span className={`
                text-xs px-1.5 py-0.5 rounded-full
                ${isSelected
                  ? 'bg-white/20 text-white'
                  : 'bg-gray-200 text-gray-500'
                }
              `}>
                {classLabel}
              </span>
            )}
          </button>
        )
      })}

      {/* Add child button */}
      <button
        onClick={onAddChild}
        className="flex items-center gap-1 px-4 py-2 rounded-full
                   text-sm font-medium whitespace-nowrap
                   border-2 border-dashed border-gray-300
                   text-gray-400 hover:border-blue-400
                   hover:text-blue-500 transition-colors"
      >
        + Add
      </button>
    </div>
  )
}

export default ChildSwitcher
