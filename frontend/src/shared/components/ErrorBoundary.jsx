import React from 'react'
import { Link } from 'react-router-dom'

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true }
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        this.setState({
            error: error,
            errorInfo: errorInfo
        })
        console.error("ErrorBoundary caught an error", error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div className="min-h-screen flex flex-col items-center justify-center bg-red-50 p-6 text-center">
                    <div className="bg-white p-8 rounded-2xl border border-red-200 shadow-sm max-w-lg w-full">
                        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6 text-3xl">
                            ⚠️
                        </div>
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong.</h1>
                        <p className="text-gray-600 mb-6">
                            We're sorry, an unexpected error occurred. Please try reloading the page or going back to the dashboard.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <button
                                onClick={() => window.location.reload()}
                                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition"
                            >
                                Reload Page
                            </button>
                            <Link
                                to="/dashboard"
                                onClick={() => this.setState({ hasError: false })}
                                className="px-6 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-medium rounded-lg transition"
                            >
                                Return to Dashboard
                            </Link>
                        </div>
                        
                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div className="mt-8 text-left bg-gray-50 p-4 rounded text-xs text-red-800 overflow-auto border border-red-100 max-h-64">
                                <p className="font-bold mb-2">{this.state.error.toString()}</p>
                                <pre>{this.state.errorInfo?.componentStack}</pre>
                            </div>
                        )}
                    </div>
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
