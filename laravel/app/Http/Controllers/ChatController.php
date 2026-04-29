<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class ChatController extends Controller
{
    private string $apiUrl;

    public function __construct()
    {
        $this->apiUrl = env('PYTHON_API_URL', 'http://127.0.0.1:5000');
    }

    public function index()
    {
        return view('chat');
    }

    public function upload(Request $request)
    {
        $request->validate([
            'file' => 'required|file|mimes:pdf,txt,docx,xlsx|max:20480',
        ]);

        $file = $request->file('file');
        $sessionId = session('python_session_id');

        $response = Http::timeout(300)
            ->attach('file', file_get_contents($file->path()), $file->getClientOriginalName())
            ->post($this->apiUrl . '/api/upload', array_filter([
                'session_id' => $sessionId,
            ]));

        if ($response->successful()) {
            $data = $response->json();
            session(['python_session_id' => $data['session_id']]);
            return response()->json($data);
        }

        return response()->json($response->json(), $response->status());
    }

    public function chat(Request $request)
    {
        $request->validate(['pergunta' => 'required|string|max:2000']);

        $sessionId = session('python_session_id');
        if (! $sessionId) {
            return response()->json(
                ['error' => 'Sessione non trovata. Carica un documento prima.'],
                404
            );
        }

        $response = Http::timeout(60)->post($this->apiUrl . '/api/chat', [
            'session_id' => $sessionId,
            'pergunta'   => $request->pergunta,
        ]);

        if ($response->successful()) {
            return response()->json($response->json());
        }

        return response()->json($response->json(), $response->status());
    }

    public function clear(Request $request)
    {
        $sessionId = session('python_session_id');

        if ($sessionId) {
            Http::timeout(10)->post($this->apiUrl . '/api/clear', [
                'session_id' => $sessionId,
            ]);
            session()->forget('python_session_id');
        }

        return response()->json(['ok' => true]);
    }
}
