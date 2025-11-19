import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Retail 360 Chatbot',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const ChatPage(),
    );
  }
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class Message {
  final String role;
  final String content;
  final List<Source>? sources;

  Message({required this.role, required this.content, this.sources});
}

class Source {
  final String? id;
  final String? type;
  final Map<String, dynamic> metadata;

  Source({this.id, this.type, required this.metadata});

  factory Source.fromJson(Map<String, dynamic> json) {
    return Source(
      id: json['id'],
      type: json['type'],
      metadata: json['metadata'] ?? {},
    );
  }
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _controller = TextEditingController();
  final List<Message> _messages = [];
  bool _isLoading = false;
  
  String get apiUrl {
    return const String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');
  }

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty) return;

    final question = _controller.text.trim();
    _controller.clear();

    setState(() {
      _messages.add(Message(role: 'user', content: question));
      _isLoading = true;
    });

    try {
      final response = await http.post(
        Uri.parse('$apiUrl/api/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'question': question,
          'history': _messages
              .where((m) => m.role != 'assistant' || m.sources == null)
              .map((m) => {'role': m.role, 'content': m.content})
              .toList(),
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final sources = (data['sources'] as List?)
            ?.map((s) => Source.fromJson(s))
            .toList();

        setState(() {
          _messages.add(Message(
            role: 'assistant',
            content: data['answer'],
            sources: sources,
          ));
        });
      } else {
        setState(() {
          _messages.add(Message(
            role: 'assistant',
            content: 'Error: ${response.statusCode} - ${response.body}',
          ));
        });
      }
    } catch (e) {
      setState(() {
        _messages.add(Message(
          role: 'assistant',
          content: 'Error al conectar con el servidor: $e',
        ));
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: const Text('Retail 360 Chatbot'),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message.role == 'user';

                return Align(
                  alignment:
                      isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.all(12),
                    constraints: BoxConstraints(
                      maxWidth: MediaQuery.of(context).size.width * 0.7,
                    ),
                    decoration: BoxDecoration(
                      color: isUser
                          ? Theme.of(context).colorScheme.primaryContainer
                          : Theme.of(context).colorScheme.secondaryContainer,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          message.content,
                          style: const TextStyle(fontSize: 16),
                        ),
                        if (message.sources != null &&
                            message.sources!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          const Divider(),
                          const Text(
                            'Fuentes:',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          ...message.sources!.map((source) {
                            return Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text(
                                '• ${source.type ?? 'N/A'}: ${source.id ?? 'N/A'}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  fontStyle: FontStyle.italic,
                                ),
                              ),
                            );
                          }),
                        ],
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      hintText: 'Escribe tu pregunta...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                    enabled: !_isLoading,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _isLoading ? null : _sendMessage,
                  icon: const Icon(Icons.send),
                  tooltip: 'Enviar',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
