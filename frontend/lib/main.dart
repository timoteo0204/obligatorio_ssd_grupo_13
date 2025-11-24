import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
        brightness: Brightness.dark,
        colorScheme:
            ColorScheme.fromSeed(
              seedColor: const Color(0xFF0D9488),
              brightness: Brightness.dark,
            ).copyWith(
              background: const Color(0xFF0F0F0F),
              surface: const Color(0xFF1E1E1E),
              primary: const Color(0xFF0D9488),
            ),
        scaffoldBackgroundColor: const Color(
          0xFF0F0F0F,
        ),
        useMaterial3: true,
        textTheme: Theme.of(context).textTheme
            .apply(
              bodyColor: Colors.grey[200],
              displayColor: Colors.grey[200],
            )
            .copyWith(
              titleLarge: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
              bodyLarge: const TextStyle(
                fontSize: 16,
                height: 1.4,
              ),
            ),
      ),
      home: const ChatApp(),
    );
  }
}

class ChatApp extends StatefulWidget {
  const ChatApp({super.key});

  @override
  State<ChatApp> createState() => _ChatAppState();
}

class Message {
  final String role;
  final String content;
  final List<Source>? sources;
  Message({
    required this.role,
    required this.content,
    this.sources,
  });
}

class Source {
  final String? id;
  final String? type;
  final Map<String, dynamic> metadata;
  Source({
    this.id,
    this.type,
    required this.metadata,
  });
  factory Source.fromJson(
    Map<String, dynamic> json,
  ) => Source(
    id: json['id'],
    type: json['type'],
    metadata: json['metadata'] ?? {},
  );
}

class ChatSummary {
  final String id;
  final String title;
  ChatSummary({
    required this.id,
    required this.title,
  });
}

class _ChatAppState extends State<ChatApp> {
  final TextEditingController _controller =
      TextEditingController();
  final FocusNode _inputFocusNode = FocusNode();
  final Map<String, List<Message>> _chatMessages =
      {};
  final List<ChatSummary> _chats = [];
  String _activeModel = "";
  String? _activeChatId;
  bool _loadingChats = false;
  final Map<String, bool> _sendingStates = {};
  final String _userId = 'user-fixed';
  final GlobalKey<ScaffoldState> _scaffoldKey =
      GlobalKey<ScaffoldState>();

  String get apiUrl =>
      const String.fromEnvironment(
        'API_URL',
        defaultValue: 'http://localhost:8000',
      );

  @override
  void initState() {
    super.initState();
    _fetchModel();
    _fetchChats();
  }

  @override
  void dispose() {
    _inputFocusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _fetchChats() async {
    setState(() => _loadingChats = true);
    try {
      final resp = await http.get(
        Uri.parse(
          '$apiUrl/api/chats?user_id=$_userId',
        ),
      );
      if (resp.statusCode == 200) {
        final data =
            jsonDecode(resp.body) as List;
        _chats.clear();
        for (var c in data) {
          _chats.add(
            ChatSummary(
              id: c['id'],
              title: c['title'],
            ),
          );
        }
      }
    } catch (_) {
    } finally {
      setState(() => _loadingChats = false);
    }
  }

  Future<void> _loadChat(String chatId) async {
    setState(() {
      _activeChatId = chatId;
      _chatMessages.putIfAbsent(chatId, () => []);
    });
    if (_chatMessages[chatId]!.isNotEmpty) return;
    try {
      final resp = await http.get(
        Uri.parse('$apiUrl/api/chats/$chatId'),
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final msgs = (data['messages'] as List)
            .map(
              (m) => Message(
                role: m['role'],
                content: m['content'],
              ),
            )
            .toList();
        setState(
          () => _chatMessages[chatId] = msgs,
        );
        _updateChatTitleIfNeeded(chatId);
      }
    } catch (_) {}
  }

  Future<void> _newChat() async {
    try {
      final resp = await http.post(
        Uri.parse('$apiUrl/api/chats'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'user_id': _userId}),
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final chatId = data['id'];
        setState(() {
          _chats.insert(
            0,
            ChatSummary(
              id: chatId,
              title: data['title'],
            ),
          );
          _chatMessages[chatId] = [];
          _activeChatId = chatId;
        });
      }
    } catch (_) {}
  }

  void _updateChatTitleIfNeeded(String chatId) {
    final chatIdx = _chats.indexWhere(
      (c) => c.id == chatId,
    );
    if (chatIdx == -1) return;
    final msgs = _chatMessages[chatId];
    if (msgs == null || msgs.isEmpty) return;
    final firstUser = msgs
        .firstWhere(
          (m) => m.role == 'user',
          orElse: () =>
              Message(role: 'user', content: ''),
        )
        .content
        .trim();
    if (firstUser.isEmpty) return;
    final truncated = firstUser.length > 50
        ? firstUser.substring(0, 47) + '...'
        : firstUser;
    if (_chats[chatIdx].title != truncated) {
      setState(
        () => _chats[chatIdx] = ChatSummary(
          id: chatId,
          title: truncated,
        ),
      );
    }
  }

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty ||
        _activeChatId == null)
      return;
    final chatId = _activeChatId!;
    final question = _controller.text.trim();
    _controller.clear();
    setState(() {
      _chatMessages[chatId]!.add(
        Message(role: 'user', content: question),
      );
      _sendingStates[chatId] = true;
    });
    try {
      final resp = await http.post(
        Uri.parse(
          '$apiUrl/api/chats/$chatId/message',
        ),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'user_id': _userId,
          'question': question,
        }),
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        final sources = (data['sources'] as List?)
            ?.map((s) => Source.fromJson(s))
            .toList();
        setState(() {
          _chatMessages[chatId]!.add(
            Message(
              role: 'assistant',
              content: data['answer'],
              sources: sources,
            ),
          );
        });
      } else {
        setState(() {
          _chatMessages[chatId]!.add(
            Message(
              role: 'assistant',
              content:
                  'Error ${resp.statusCode}: ${resp.body}',
            ),
          );
        });
      }
    } catch (e) {
      setState(() {
        _chatMessages[chatId]!.add(
          Message(
            role: 'assistant',
            content: 'Error: $e',
          ),
        );
      });
    } finally {
      setState(
        () => _sendingStates[chatId] = false,
      );
    }
    _updateChatTitleIfNeeded(chatId);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isMobile =
            constraints.maxWidth < 700;
        final sidebar = Container(
          width: 280,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [
                Color(0xFF141414),
                Color(0xFF101010),
              ],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
            border: Border(
              right: BorderSide(
                color: Color(0xFF1F1F1F),
                width: 0.5,
              ),
            ),
          ),
          child: Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              SafeArea(
                bottom: false,
                child: Padding(
                  padding:
                      const EdgeInsets.fromLTRB(
                        16,
                        16,
                        12,
                        8,
                      ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Conversaciones',
                          style: Theme.of(
                            context,
                          ).textTheme.titleLarge,
                        ),
                      ),
                      Tooltip(
                        message: 'Nuevo chat',
                        child: IconButton(
                          onPressed: _newChat,
                          icon: const Icon(
                            Icons
                                .add_circle_outline,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (_loadingChats)
                const LinearProgressIndicator(
                  minHeight: 2,
                ),
              Expanded(
                child: ListView.builder(
                  padding:
                      const EdgeInsets.symmetric(
                        horizontal: 8,
                      ),
                  itemCount: _chats.length,
                  itemBuilder: (c, i) {
                    final chat = _chats[i];
                    final active =
                        chat.id == _activeChatId;
                    return InkWell(
                      onTap: () =>
                          _loadChat(chat.id),
                      borderRadius:
                          BorderRadius.circular(
                            10,
                          ),
                      child: Container(
                        margin:
                            const EdgeInsets.symmetric(
                              vertical: 4,
                              horizontal: 4,
                            ),
                        padding:
                            const EdgeInsets.symmetric(
                              vertical: 10,
                              horizontal: 12,
                            ),
                        decoration: BoxDecoration(
                          color: active
                              ? const Color(
                                  0xFF1E1E1E,
                                )
                              : const Color(
                                  0xFF181818,
                                ),
                          borderRadius:
                              BorderRadius.circular(
                                10,
                              ),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons
                                  .chat_bubble_outline,
                              size: 18,
                              color: Colors.grey,
                            ),
                            const SizedBox(
                              width: 8,
                            ),
                            Expanded(
                              child: Text(
                                chat.title.isEmpty
                                    ? 'Chat'
                                    : chat.title,
                                maxLines: 1,
                                overflow:
                                    TextOverflow
                                        .ellipsis,
                                style:
                                    const TextStyle(
                                      fontSize:
                                          14,
                                    ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(
                  12.0,
                ),
                child: OutlinedButton.icon(
                  onPressed: _fetchChats,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Refrescar'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Theme.of(
                      context,
                    ).colorScheme.primary,
                  ),
                ),
              ),
            ],
          ),
        );
        final chatArea = Column(
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(
                20,
                14,
                20,
                12,
              ),
              decoration: const BoxDecoration(
                color: Color(0xFF131313),
                border: Border(
                  bottom: BorderSide(
                    color: Color(0xFF1F1F1F),
                    width: 0.5,
                  ),
                ),
              ),
              child: Row(
                children: [
                  if (isMobile)
                    IconButton(
                      icon: const Icon(
                        Icons.menu,
                      ),
                      onPressed: () =>
                          _scaffoldKey
                              .currentState
                              ?.openDrawer(),
                    ),
                  const SizedBox(width: 4),
                  const Text(
                    'Retail 360',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _activeModel,
                      style: TextStyle(
                        color: Colors.grey,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _activeChatId == null
                  ? const Center(
                      child: Text(
                        'Seleccioná o creá un chat',
                      ),
                    )
                  : ListView.builder(
                      padding:
                          const EdgeInsets.fromLTRB(
                            20,
                            16,
                            20,
                            160,
                          ),
                      itemCount:
                          _chatMessages[_activeChatId!]!
                              .length,
                      itemBuilder: (context, index) {
                        final m =
                            _chatMessages[_activeChatId!]![index];
                        final isUser =
                            m.role == 'user';
                        return Container(
                          margin:
                              const EdgeInsets.only(
                                bottom: 12,
                              ),
                          child: Row(
                            crossAxisAlignment:
                                CrossAxisAlignment
                                    .start,
                            mainAxisAlignment:
                                isUser
                                ? MainAxisAlignment
                                      .end
                                : MainAxisAlignment
                                      .start,
                            children: [
                              if (!isUser)
                                const CircleAvatar(
                                  radius: 14,
                                  child: Icon(
                                    Icons
                                        .smart_toy,
                                    size: 16,
                                  ),
                                ),
                              if (!isUser)
                                const SizedBox(
                                  width: 10,
                                ),
                              Flexible(
                                child: Container(
                                  padding:
                                      const EdgeInsets.symmetric(
                                        vertical:
                                            10,
                                        horizontal:
                                            14,
                                      ),
                                  decoration: BoxDecoration(
                                    color: isUser
                                        ? const Color(
                                            0xFF0D9488,
                                          )
                                        : const Color(
                                            0xFF1F1F1F,
                                          ),
                                    borderRadius:
                                        BorderRadius.circular(
                                          16,
                                        ),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors
                                            .black
                                            .withOpacity(
                                              0.3,
                                            ),
                                        blurRadius:
                                            4,
                                        offset:
                                            const Offset(
                                              0,
                                              2,
                                            ),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment
                                            .start,
                                    children: [
                                      Text(
                                        m.content,
                                        style: TextStyle(
                                          color:
                                              isUser
                                              ? Colors.white
                                              : Colors.grey[200],
                                        ),
                                      ),
                                      if (m.sources !=
                                              null &&
                                          m
                                              .sources!
                                              .isNotEmpty) ...[
                                        const SizedBox(
                                          height:
                                              8,
                                        ),
                                        const Text(
                                          'Fuentes:',
                                          style: TextStyle(
                                            fontWeight:
                                                FontWeight.bold,
                                            fontSize:
                                                12,
                                          ),
                                        ),
                                        ...m.sources!.map(
                                          (
                                            s,
                                          ) => Text(
                                            '• ${s.type ?? 'N/A'}: ${s.id ?? 'N/A'}',
                                            style: const TextStyle(
                                              fontSize:
                                                  12,
                                              fontStyle:
                                                  FontStyle.italic,
                                            ),
                                          ),
                                        ),
                                      ],
                                      const SizedBox(
                                        height: 4,
                                      ),
                                      Text(
                                        DateTime.now()
                                            .toLocal()
                                            .toString()
                                            .substring(
                                              11,
                                              16,
                                            ),
                                        style: const TextStyle(
                                          color: Colors
                                              .grey,
                                          fontSize:
                                              10,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              if (isUser)
                                const SizedBox(
                                  width: 10,
                                ),
                              if (isUser)
                                const CircleAvatar(
                                  radius: 14,
                                  child: Icon(
                                    Icons.person,
                                    size: 16,
                                  ),
                                ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
        return Scaffold(
          key: _scaffoldKey,
          drawer: isMobile
              ? Drawer(child: sidebar)
              : null,
          body: Stack(
            children: [
              Row(
                children: [
                  if (!isMobile) sidebar,
                  Expanded(child: chatArea),
                ],
              ),
              Positioned(
                left: isMobile ? 0 : 280,
                right: 0,
                bottom: 0,
                child: Container(
                  padding:
                      const EdgeInsets.fromLTRB(
                        20,
                        12,
                        20,
                        20,
                      ),
                  decoration: const BoxDecoration(
                    color: Color(0xFF121212),
                    border: Border(
                      top: BorderSide(
                        color: Color(0xFF1F1F1F),
                        width: 0.5,
                      ),
                    ),
                  ),
                  child: Column(
                    mainAxisSize:
                        MainAxisSize.min,
                    children: [
                      Row(
                        crossAxisAlignment:
                            CrossAxisAlignment
                                .end,
                        children: [
                          Expanded(
                            child: ConstrainedBox(
                              constraints:
                                  const BoxConstraints(
                                    maxHeight:
                                        180,
                                  ),
                              child: Scrollbar(
                                child: RawKeyboardListener(
                                  focusNode:
                                      _inputFocusNode,
                                  onKey: (event) {
                                    if (event
                                        is RawKeyDownEvent) {
                                      final isEnter =
                                          event
                                              .logicalKey ==
                                          LogicalKeyboardKey
                                              .enter;
                                      final isShift =
                                          event
                                              .isShiftPressed;
                                      if (isEnter &&
                                          !isShift) {
                                        if (!(_sendingStates[_activeChatId] ??
                                                false) &&
                                            _activeChatId !=
                                                null) {
                                          if (_controller
                                              .text
                                              .trim()
                                              .isNotEmpty) {
                                            _sendMessage();
                                          }
                                        }
                                      }
                                    }
                                  },
                                  child: TextField(
                                    controller:
                                        _controller,
                                    enabled:
                                        !(_sendingStates[_activeChatId] ??
                                            false) &&
                                        _activeChatId !=
                                            null,
                                    maxLines:
                                        null,
                                    decoration: InputDecoration(
                                      hintText:
                                          _activeChatId ==
                                              null
                                          ? 'Crea un chat para comenzar'
                                          : 'Escribe tu mensaje...',
                                      filled:
                                          true,
                                      fillColor:
                                          const Color(
                                            0xFF1A1A1A,
                                          ),
                                      contentPadding: const EdgeInsets.symmetric(
                                        vertical:
                                            12,
                                        horizontal:
                                            14,
                                      ),
                                      border: OutlineInputBorder(
                                        borderRadius:
                                            BorderRadius.circular(
                                              14,
                                            ),
                                        borderSide: const BorderSide(
                                          color: Color(
                                            0xFF2A2A2A,
                                          ),
                                        ),
                                      ),
                                      enabledBorder: OutlineInputBorder(
                                        borderRadius:
                                            BorderRadius.circular(
                                              14,
                                            ),
                                        borderSide: const BorderSide(
                                          color: Color(
                                            0xFF2A2A2A,
                                          ),
                                        ),
                                      ),
                                      focusedBorder: OutlineInputBorder(
                                        borderRadius:
                                            BorderRadius.circular(
                                              14,
                                            ),
                                        borderSide: BorderSide(
                                          color: Theme.of(
                                            context,
                                          ).colorScheme.primary,
                                          width:
                                              1.4,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(
                            width: 12,
                          ),
                          SizedBox(
                            height: 48,
                            width: 48,
                            child: ElevatedButton(
                              onPressed:
                                  (!(_sendingStates[_activeChatId] ??
                                          false) &&
                                      _activeChatId !=
                                          null)
                                  ? _sendMessage
                                  : null,
                              style: ElevatedButton.styleFrom(
                                padding:
                                    EdgeInsets
                                        .zero,
                                backgroundColor:
                                    Theme.of(
                                          context,
                                        )
                                        .colorScheme
                                        .primary,
                                shape: RoundedRectangleBorder(
                                  borderRadius:
                                      BorderRadius.circular(
                                        14,
                                      ),
                                ),
                              ),
                              child:
                                  (_sendingStates[_activeChatId] ??
                                      false)
                                  ? const Padding(
                                      padding:
                                          EdgeInsets.all(
                                            8.0,
                                          ),
                                      child: CircularProgressIndicator(
                                        strokeWidth:
                                            2,
                                        valueColor:
                                            AlwaysStoppedAnimation(
                                              Colors.white,
                                            ),
                                      ),
                                    )
                                  : const Icon(
                                      Icons
                                          .send_rounded,
                                      color: Colors
                                          .white,
                                    ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Align(
                        alignment:
                            Alignment.centerLeft,
                        child: Text(
                          'El modelo puede cometer errores. Verifica la información importante.',
                          style: TextStyle(
                            color: Colors.grey,
                            fontSize: 11,
                          ),
                        ),
                      ),
                      const SizedBox(height: 4),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _fetchModel() async {
    final url = Uri.parse('$apiUrl/api/model');
    await http
        .get(url)
        .then((response) {
          if (response.statusCode == 200) {
            final data = jsonDecode(
              response.body,
            );
            setState(() {
              _activeModel = data['model'];
            });
          }
        })
        .catchError((error) {});
  }
}
