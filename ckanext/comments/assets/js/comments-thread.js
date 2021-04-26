ckan.module("comments-thread", function ($) {
  "use strict";

  return {
    options: {
      subjectId: null,
      subjectType: null,
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.$(".comment-actions .remove-comment").on(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").on(
        "click",
        this._onApproveComment
      );
      this.$(".comment-actions .reply-to-comment").on(
        "click",
        this._onReplyToComment
      );
      this.$(".comment-actions .edit-comment").on("click", this._onEditComment);
      this.$(".comment-actions .save-comment").on("click", this._onSaveComment);
      this.$(".comment-footer").on("click", this._onFooterClick);
      this.$(".comment-form").on("submit", this._onSubmit);
    },
    teardown: function () {
      this.$(".comment-action.remove-comment").off(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").off(
        "click",
        this._onApproveComment
      );

      this.$("comment-form").off("sumbit", this._onSubmit);
    },
    _onFooterClick: function (e) {
      if (e.target.classList.contains("cancel-reply")) {
        this._disableActiveReply();
      } else if (e.target.classList.contains("save-reply")) {
        var content = e.currentTarget.querySelector(
          ".reply-textarea-wrapper textarea"
        ).value;
        this._saveComment({
          content: content,
          reply_to_id: e.target.dataset.id,
        });
      }
    },
    _onRemoveComment: function (e) {
      var id = e.currentTarget.dataset.id;

      this.sandbox.client.call(
        "POST",
        "comments_comment_delete",
        {
          id: id,
        },
        function () {
          window.location.reload();
        }
      );
    },
    _onApproveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      this.sandbox.client.call(
        "POST",
        "comments_comment_approve",
        {
          id: id,
        },
        function () {
          window.location.reload();
        }
      );
    },

    _disableActiveReply: function () {
      $(".comment .reply-textarea-wrapper").remove();
    },
    _onReplyToComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var id = e.currentTarget.dataset.id;
      var comment = $(e.currentTarget).closest(".comment");
      var textarea = $('<textarea rows="5" class="form-control">');
      comment.find(".comment-footer").append(
        $('<div class="control-full reply-textarea-wrapper">').append(
          textarea,
          $("<div>")
            .addClass("reply-actions")
            .append(
              $("<button>", { text: this._("Reply"), "data-id": id }).addClass(
                "btn btn-default reply-action save-reply"
              ),
              $("<button>", { text: this._("Cancel") }).addClass(
                "btn btn-danger reply-action cancel-reply"
              )
            )
        )
      );
    },
    _disableActiveEdit: function () {
      $(".comment.edit-in-progress")
        .removeClass(".edit-in-progress")
        .find(".comment-action.save-comment")
        .addClass("hidden")
        .prevObject.find(".comment-action.edit-comment")
        .removeClass("hidden")
        .prevObject.find(".edit-textarea-wrapper")
        .remove()
        .prevObject.find(".comment-content")
        .removeClass("hidden");
    },
    _onEditComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var target = $(e.currentTarget).addClass("hidden");
      target.parent().find(".save-comment").removeClass("hidden");
      var content = target
        .closest(".comment")
        .addClass("edit-in-progress")
        .find(".comment-content");
      var textarea = $('<textarea rows="5" class="form-control">');
      textarea.text(content.text());
      content
        .addClass("hidden")
        .parent()
        .append(
          $('<div class="control-full edit-textarea-wrapper">').append(textarea)
        );
    },
    _onSaveComment: function (e) {
      var self = this;
      var id = e.currentTarget.dataset.id;
      var target = $(e.currentTarget);
      var notify = this.sandbox.notify;
      var _ = this.sandbox.translate;
      var content = target.closest(".comment").find(".comment-body textarea");
      this.sandbox.client.call(
        "POST",
        "comments_comment_update",
        {
          id: id,
          content: content.val(),
        },
        function () {
          window.location.reload();
        },
        function (err) {
          console.log(err);
          var oldEl = notify.el;
          notify.el = target.closest(".comment");
          notify(
            self._("An Error Occurred").fetch(),
            self._("Comment cannot be updated").fetch(),
            "error"
          );
          notify.el.find(".alert .close").attr("data-dismiss", "alert");
          notify.el = oldEl;
        }
      );
    },
    _onSubmit: function (e) {
      e.preventDefault();
      var data = new FormData(e.target);
      this._saveComment({ content: data.get("content"), create_thread: true });
    },
    _saveComment: function (data) {
      data.subject_id = this.options.subjectId;
      data.subject_type = this.options.subjectType;
      this.sandbox.client.call(
        "POST",
        "comments_comment_create",
        data,
        function () {
          window.location.reload();
        }
      );
    },
  };
});
