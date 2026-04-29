<?php

use App\Http\Controllers\ChatController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ChatController::class, 'index']);
Route::post('/upload', [ChatController::class, 'upload']);
Route::post('/chat', [ChatController::class, 'chat']);
Route::post('/clear', [ChatController::class, 'clear']);
