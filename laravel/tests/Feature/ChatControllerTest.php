<?php

namespace Tests\Feature;

use Illuminate\Http\UploadedFile;
use Tests\TestCase;

class ChatControllerTest extends TestCase
{
    public function test_index_devolve_view_chat(): void
    {
        $response = $this->get('/');
        $response->assertStatus(200);
        $response->assertViewIs('chat');
    }

    public function test_upload_valida_ficheiro_obrigatorio(): void
    {
        $response = $this->postJson('/upload');
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_upload_valida_extensao(): void
    {
        $file = UploadedFile::fake()->create('dados.csv', 100, 'text/csv');
        $response = $this->postJson('/upload', ['file' => $file]);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_upload_valida_tamanho_maximo(): void
    {
        $file = UploadedFile::fake()->create('grande.pdf', 25000, 'application/pdf');
        $response = $this->postJson('/upload', ['file' => $file]);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['file']);
    }

    public function test_chat_valida_pergunta_obrigatoria(): void
    {
        $response = $this->postJson('/chat', []);
        $response->assertStatus(422);
        $response->assertJsonValidationErrors(['pergunta']);
    }

    public function test_clear_sem_sessao_devolve_ok(): void
    {
        $response = $this->postJson('/clear');
        $response->assertStatus(200);
        $response->assertJson(['ok' => true]);
    }
}
