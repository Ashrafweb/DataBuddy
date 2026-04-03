"use client";

import { useState, useRef, useEffect } from "react";
import axios from "axios";
import {
	Database,
	Play,
	Copy,
	Loader2,
	AlertCircle,
	CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Home() {
	const [messages, setMessages] = useState([]);
	const [question, setQuestion] = useState("");
	const [loading, setLoading] = useState(false);
	const [tables, setTables] = useState([]);
	const messagesEndRef = useRef(null);

	useEffect(() => {
		fetchTables();
	}, []);

	useEffect(() => {
		if (messagesEndRef.current) {
			messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
		}
	}, [messages]);

	const fetchTables = async () => {
		try {
			const response = await axios.get(`${API}/tables`);
			setTables(response.data);
		} catch (error) {
			console.error("Failed to fetch tables:", error);
		}
	};

	const handleSubmit = async (e) => {
		e.preventDefault();
		const questionText = question.trim();
		if (!questionText || loading) return;

		const userMessage = { type: "user", content: questionText };
		const newMessages = messages.slice();
		newMessages.push(userMessage);
		setMessages(newMessages);
		setQuestion("");
		setLoading(true);

		try {
			const response = await axios.post(`${API}/query`, {
				question: questionText,
				session_id: "demo-session",
			});

			const aiMessage = {
				type: "ai",
				sql: response.data.sql,
				results: response.data.results,
				row_count: response.data.row_count,
				execution_time_ms: response.data.execution_time_ms,
			};

			const updatedMessages = newMessages.slice();
			updatedMessages.push(aiMessage);
			setMessages(updatedMessages);
			toast.success(
				`Query executed successfully (${response.data.execution_time_ms}ms)`,
			);
		} catch (error) {
			const errorMsg = error.response
				? error.response.data
					? error.response.data.detail
					: "Failed to execute query"
				: "Failed to execute query";
			const errorMessage = {
				type: "error",
				content: errorMsg,
			};
			const updatedMessages = newMessages.slice();
			updatedMessages.push(errorMessage);
			setMessages(updatedMessages);
			toast.error("Query failed");
		} finally {
			setLoading(false);
		}
	};

	const copyToClipboard = (text) => {
		navigator.clipboard.writeText(text);
		toast.success("Copied to clipboard");
	};

	const renderMessage = (message, index) => {
		if (message.type === "user") {
			return (
				<div key={index} className='flex justify-end'>
					<div
						className='bg-zinc-800 text-zinc-100 rounded-2xl rounded-tr-sm px-5 py-3 max-w-[80%]'
						data-testid='user-message'
					>
						<p className='text-base'>{message.content}</p>
					</div>
				</div>
			);
		}

		if (message.type === "ai") {
			const hasResults = message.results && message.results.length > 0;
			const firstRow = hasResults ? message.results[0] : null;
			const columnKeys = firstRow ? Object.keys(firstRow) : [];

			return (
				<div
					key={index}
					className='border-l-2 border-cyan-500 pl-4'
					data-testid='ai-message'
				>
					<div className='space-y-4'>
						<div
							className='bg-zinc-900/50 border border-zinc-800 rounded-md p-4'
							data-testid='sql-block'
						>
							<div className='flex items-center justify-between mb-3'>
								<span className='text-xs font-semibold text-amber-400 uppercase tracking-wide'>
									Generated SQL
								</span>
								<Button
									size='sm'
									variant='ghost'
									onClick={() => copyToClipboard(message.sql)}
									className='h-7 text-xs text-zinc-400 hover:text-white'
									data-testid='copy-sql-button'
								>
									<Copy className='w-3 h-3 mr-1' />
									Copy
								</Button>
							</div>
							<pre className='text-sm font-mono text-zinc-300 overflow-x-auto'>
								<code>{message.sql}</code>
							</pre>
						</div>

						{hasResults && (
							<div
								className='bg-zinc-900/30 border border-zinc-800 rounded-md p-4'
								data-testid='results-table'
							>
								<div className='flex items-center justify-between mb-3'>
									<div className='flex items-center gap-2'>
										<CheckCircle2 className='w-4 h-4 text-green-500' />
										<span className='text-sm text-zinc-400'>
											{message.row_count} rows • {message.execution_time_ms}ms
										</span>
									</div>
								</div>
								<div className='overflow-x-auto rounded-md border border-zinc-800'>
									<Table>
										<TableHeader>
											<TableRow>
												{columnKeys.map((key) => (
													<TableHead
														key={key}
														className='font-mono text-xs text-zinc-400 bg-zinc-900/50'
													>
														{key}
													</TableHead>
												))}
											</TableRow>
										</TableHeader>
										<TableBody>
											{message.results.map((row, rowIndex) => (
												<TableRow key={rowIndex}>
													{columnKeys.map((key) => (
														<TableCell
															key={key}
															className='font-mono text-sm text-zinc-300'
														>
															{row[key] !== null ? String(row[key]) : "null"}
														</TableCell>
													))}
												</TableRow>
											))}
										</TableBody>
									</Table>
								</div>
							</div>
						)}

						{message.results && message.results.length === 0 && (
							<Alert className='bg-zinc-900/50 border-zinc-800'>
								<AlertCircle className='h-4 w-4 text-amber-500' />
								<AlertDescription className='text-zinc-400'>
									Query executed successfully but returned no results.
								</AlertDescription>
							</Alert>
						)}
					</div>
				</div>
			);
		}

		if (message.type === "error") {
			return (
				<div key={index} data-testid='error-message'>
					<Alert className='bg-red-950/20 border-red-900/50'>
						<AlertCircle className='h-4 w-4 text-red-500' />
						<AlertDescription className='text-red-300'>
							{message.content}
						</AlertDescription>
					</Alert>
				</div>
			);
		}

		return null;
	};

	return (
		<div className='App flex h-screen overflow-hidden'>
			<Toaster position='top-right' theme='dark' />

			<aside className='hidden md:flex w-64 border-r border-zinc-800 flex-col bg-zinc-950/50 backdrop-blur-xl'>
				<div className='p-6 border-b border-zinc-800'>
					<div className='flex items-center gap-3'>
						<div className='p-2 bg-amber-500/10 rounded-md'>
							<Database className='w-6 h-6 text-amber-500' />
						</div>
						<div>
							<h1 className='text-lg font-heading font-semibold text-zinc-100'>
								SQL Agent
							</h1>
							<p className='text-xs text-zinc-500'>Powered by Gemini</p>
						</div>
					</div>
				</div>

				<ScrollArea className='flex-1 p-4'>
					<div className='space-y-4'>
						<div>
							<h3 className='text-sm font-semibold text-zinc-400 mb-2'>
								Available Tables
							</h3>
							{tables.length === 0 ? (
								<p className='text-xs text-zinc-600'>No tables found</p>
							) : (
								<div className='space-y-2'>
									{tables.map((table) => (
										<div
											key={table.table_name}
											className='p-2 bg-zinc-900/50 rounded-md border border-zinc-800/50'
										>
											<p className='text-sm font-mono text-amber-400'>
												{table.table_name}
											</p>
											<p className='text-xs text-zinc-600 mt-1'>
												{table.columns.length} columns
											</p>
										</div>
									))}
								</div>
							)}
						</div>
					</div>
				</ScrollArea>
			</aside>

			<main className='flex-1 flex flex-col relative overflow-hidden'>
				<header className='border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md p-4'>
					<h2 className='text-xl font-heading font-semibold text-zinc-100'>
						Ask your database
					</h2>
					<p className='text-sm text-zinc-500'>
						Ask questions in natural language
					</p>
				</header>

				<ScrollArea className='flex-1 p-6 pb-32'>
					<div className='max-w-4xl mx-auto space-y-6'>
						{messages.length === 0 && (
							<div className='text-center py-12'>
								<div className='inline-flex p-4 bg-zinc-900/50 rounded-full mb-4'>
									<Database className='w-12 h-12 text-zinc-600' />
								</div>
								<h3 className='text-xl font-heading font-semibold text-zinc-300 mb-2'>
									Start querying your database
								</h3>
								<p className='text-zinc-500'>
									Ask any question about your data in plain English
								</p>
							</div>
						)}

						{messages.map(renderMessage)}

						{loading && (
							<div
								className='border-l-2 border-cyan-500 pl-4'
								data-testid='loading-indicator'
							>
								<div className='flex items-center gap-3 text-cyan-400'>
									<Loader2 className='w-5 h-5 animate-spin' />
									<span className='text-sm'>Generating SQL query...</span>
								</div>
							</div>
						)}

						<div ref={messagesEndRef} />
					</div>
				</ScrollArea>

				<div className='input-area p-6'>
					<form onSubmit={handleSubmit} className='max-w-4xl mx-auto'>
						<div className='flex gap-3'>
							<Textarea
								value={question}
								onChange={(e) => setQuestion(e.target.value)}
								placeholder='Ask a question about your database...'
								className='flex-1 bg-zinc-900 border-zinc-700 focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 resize-none min-h-[60px] text-base placeholder:text-zinc-600'
								disabled={loading}
								onKeyDown={(e) => {
									if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
										handleSubmit(e);
									}
								}}
								data-testid='query-input'
							/>
							<Button
								type='submit'
								disabled={loading || !question.trim()}
								className='bg-amber-500 text-zinc-950 hover:bg-amber-400 font-medium h-auto px-6'
								data-testid='submit-button'
							>
								{loading ? (
									<Loader2 className='w-5 h-5 animate-spin' />
								) : (
									<>
										<Play className='w-5 h-5 mr-2' />
										Execute
									</>
								)}
							</Button>
						</div>
						<p className='text-xs text-zinc-600 mt-2'>
							Press Cmd+Enter to submit
						</p>
					</form>
				</div>
			</main>
		</div>
	);
}
