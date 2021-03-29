ckan.module("comments-thread", function ($, _) {
  "use strict";

  return {
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
      this.$(".comment-actions .edit-comment").on("click", this._onEditComment);
      this.$(".comment-actions .save-comment").on("click", this._onSaveComment);
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
    _onEditComment: function (e) {
      var target = $(e.currentTarget).hide();
      target.parent().find(".save-comment").removeClass("hidden");
      var content = target.closest(".comment").find(".comment-content");
      console.log(content.text());
      var textarea = $('<textarea rows="5" class="form-control">');
      textarea.text(content.text());
      content.replaceWith($('<div class="control-full">').append(textarea));
    },
    _onSaveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      var target = $(e.currentTarget);
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
        }
      );
    },
    _onSubmit: function (e) {
      e.preventDefault();
      var data = new FormData(e.target);

      this.sandbox.client.call(
        "POST",
        "comments_comment_create",
        {
          content: data.get("content"),
          subject_id: data.get("subject_id"),
          subject_type: data.get("subject_type"),
          create_thread: true,
        },
        function () {
          window.location.reload();
        }
      );
    },
  };
});
